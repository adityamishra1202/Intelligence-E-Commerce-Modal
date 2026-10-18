"""POST /api/chat/ end to end with the LLM and embeddings faked."""
from unittest import expectedFailure

import httpx
import openai
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from assistant.tests.factories import build_catalog
from assistant.tests.fakes import embed_products, extraction, patch_embeddings, patch_llm, route
from conversations.models import Conversation, Message
from products.models import Product

URL = "/api/chat/"
HEADPHONES = extraction(keywords=["headphones"], category="headphones")


def connection_error():
    return openai.APIConnectionError(request=httpx.Request("POST", "http://localhost:11434/v1/chat/completions"))


class ChatAPITestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.c = build_catalog()
        cls.usd = cls.c["usd_site"].id
        cls.inr = cls.c["inr_site"].id
        embed_products(Product.objects.all())

    def setUp(self):
        cache.clear()  # throttling state
        self.client = APIClient()

    def chat(self, message, website_ids=None, conversation_id=None, client=None, llm=None):
        body = {"message": message, "website_ids": website_ids or [self.usd]}
        if conversation_id is not None:
            body["conversation_id"] = conversation_id
        with patch_llm(default=llm or route(HEADPHONES)) as fake, patch_embeddings():
            response = (client or self.client).post(URL, body, format="json")
        response.fake = fake
        return response


class ChatValidationTests(ChatAPITestBase):
    def test_invalid_body(self):
        self.assertEqual(self.client.post(URL, "not json", content_type="application/json").status_code, 400)

    def test_missing_message(self):
        self.assertEqual(self.client.post(URL, {"website_ids": [self.usd]}, format="json").status_code, 400)

    def test_empty_website_ids(self):
        self.assertEqual(self.client.post(URL, {"message": "hi", "website_ids": []}, format="json").status_code, 400)

    def test_unknown_website(self):
        self.assertEqual(self.chat("headphones", website_ids=[99999]).status_code, 400)

    def test_inactive_website(self):
        site = self.c["inr_site"]
        site.is_active = False
        site.save()
        self.assertEqual(self.chat("headphones", website_ids=[site.id]).status_code, 400)

    def test_unknown_conversation(self):
        self.assertEqual(self.chat("headphones", conversation_id=99999).status_code, 404)

    def test_scope_mismatch(self):
        first = self.chat("Suggest headphones under $350").json()
        response = self.chat("and laptops?", website_ids=[self.usd, self.inr], conversation_id=first["conversation_id"])
        self.assertEqual(response.status_code, 404)

    def test_error_responses_carry_codes(self):
        self.assertEqual(self.client.post(URL, {}, format="json").json().get("code"), "invalid_request")
        self.assertEqual(self.chat("x", website_ids=[99999]).json().get("code"), "website_unavailable")
        self.assertEqual(self.chat("x", conversation_id=99999).json().get("code"), "conversation_not_found")


class ChatFlowTests(ChatAPITestBase):
    def test_success_shape(self):
        response = self.chat("Suggest headphones under $350")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        for key in ("conversation_id", "message", "intent", "answer", "requirements", "total_products", "products"):
            self.assertIn(key, body)
        self.assertTrue(body["products"])
        self.assertTrue(all(float(p["price"]) <= 350 for p in body["products"]))

    def test_no_match_is_explained_without_model_answer(self):
        response = self.chat("headphones under $10")
        body = response.json()
        self.assertEqual(body["products"], [])
        self.assertIn("Raise your budget", body["answer"])
        answer_calls = [c for c in response.fake.calls if "extract" not in c["messages"][0]["content"].lower()]
        self.assertEqual(answer_calls, [])

    def test_both_messages_persisted_and_conversation_reused(self):
        first = self.chat("Suggest headphones under $350").json()
        second = self.chat("Which has the best rating?", conversation_id=first["conversation_id"]).json()
        self.assertEqual(first["conversation_id"], second["conversation_id"])
        roles = list(Message.objects.filter(conversation_id=first["conversation_id"])
                     .order_by("id").values_list("role", flat=True))
        self.assertEqual(roles, ["user", "assistant", "user", "assistant"])

    def test_two_conversations_never_share_history(self):
        self.chat("Suggest headphones under $350")
        response = self.chat("Show me laptops", llm=route(extraction(category="laptop", keywords=["laptop"])))
        extraction_prompts = [c for c in response.fake.calls if "extract" in c["messages"][0]["content"].lower()]
        self.assertTrue(extraction_prompts)
        text = "\n".join(m["content"] for m in extraction_prompts[0]["messages"])
        self.assertNotIn("headphones under $350", text)

    def test_provider_error_is_safe(self):
        response = self.chat("Suggest headphones under $350", llm=connection_error())
        self.assertGreaterEqual(response.status_code, 500)
        text = response.content.decode()
        self.assertNotIn("Traceback", text)
        self.assertNotIn("APIConnectionError", text)
        self.assertNotIn("11434", text)

    def test_failure_saves_nothing(self):
        before = (Conversation.objects.count(), Message.objects.count())
        self.chat("Suggest headphones under $350", llm=connection_error())
        self.assertEqual((Conversation.objects.count(), Message.objects.count()), before)

    def test_request_without_search_terms_does_not_fail(self):
        response = self.chat("show me something", llm=route(extraction()))
        self.assertEqual(response.status_code, 200)

    def test_embedding_outage_adds_notice_and_still_answers(self):
        body = {"message": "Suggest headphones under $350", "website_ids": [self.usd]}
        with patch_llm(default=route(HEADPHONES)), patch_embeddings(side_effect=RuntimeError("Ollama down")):
            response = self.client.post(URL, body, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["products"])
        self.assertIn("Semantic ranking was unavailable; results use standard ranking.", response.json()["notices"])

    def test_provider_unreachable_is_503(self):
        response = self.chat("Suggest headphones under $350", llm=connection_error())
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json().get("code"), "model_unavailable")


class ChatIntentTests(ChatAPITestBase):
    def test_unrelated_request_is_redirected_without_llm(self):
        response = self.chat("write a python script to sort a list")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["intent"], "out_of_scope")
        self.assertEqual(response.fake.calls, [])

    def test_general_shopping_question_is_answered(self):
        llm = route(extraction(intent="general_question"), answer="General advice (not specific to products in the catalog): look at comfort.")
        response = self.chat("Is noise cancellation worth it for flights?", llm=llm)
        body = response.json()
        self.assertEqual(body["intent"], "general_question")
        self.assertIn("General advice", body["answer"])

    def test_greeting_needs_no_model_call(self):
        response = self.chat("hello")
        self.assertEqual(response.json()["intent"], "general_question")
        self.assertEqual(response.fake.calls, [])

    def test_shopping_word_keeps_request_in_scope(self):
        response = self.chat("best laptop for python programming under $1200",
                             llm=route(extraction(category="laptop", keywords=["laptop"])))
        self.assertEqual(response.json()["intent"], "product_search")

    def test_model_classified_out_of_scope_is_redirected(self):
        response = self.chat("tell me about the weather on mars",
                             llm=route(extraction(intent="out_of_scope")))
        body = response.json()
        self.assertEqual(body["intent"], "out_of_scope")
        self.assertEqual(body["products"], [])

    def test_advice_with_code_is_replaced_by_redirect(self):
        llm = route(extraction(intent="general_question"), answer="```python\nprint(1)\n```")
        body = self.chat("how do I choose a keyboard?", llm=llm).json()
        self.assertNotIn("```", body["answer"])
        self.assertIn("shopping assistant", body["answer"])

    def test_general_question_does_not_erase_memory(self):
        first = self.chat("Suggest headphones under $350").json()
        conversation = Conversation.objects.get(id=first["conversation_id"])
        saved = dict(conversation.current_requirements)
        self.chat("hello", conversation_id=first["conversation_id"],
                  llm=route(extraction(intent="general_question"), answer="Hi"))
        conversation.refresh_from_db()
        self.assertEqual(conversation.current_requirements, saved)


class ChatOwnershipTests(ChatAPITestBase):
    @expectedFailure  # flips in Phase 3.10 (conversation ownership)
    def test_other_session_cannot_continue_conversation(self):
        first = self.chat("Suggest headphones under $350").json()
        stranger = APIClient()
        response = self.chat("Which has the best rating?", conversation_id=first["conversation_id"], client=stranger)
        self.assertEqual(response.status_code, 404)
