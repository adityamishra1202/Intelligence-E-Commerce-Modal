"""GET /api/conversations/ and /api/conversations/<id>/ contract and ownership."""
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from assistant.tests.factories import build_catalog
from assistant.tests.fakes import extraction, patch_embeddings, patch_llm, route
from conversations.models import Conversation

HEADPHONES = extraction(category="headphones", keywords=["headphones"])


class ConversationAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.catalog = build_catalog()
        cls.site = cls.catalog["usd_site"].id

    def setUp(self):
        cache.clear()
        self.owner = APIClient()

    def chat(self, client, message, conversation_id=None):
        body = {"message": message, "website_ids": [self.site]}
        if conversation_id:
            body["conversation_id"] = conversation_id
        with patch_llm(default=route(HEADPHONES)), patch_embeddings():
            return client.post("/api/chat/", body, format="json").json()

    def test_list_shape_newest_first_and_only_own(self):
        first = self.chat(self.owner, "Suggest headphones under $350")
        second = self.chat(self.owner, "Suggest headphones under $100")
        self.chat(APIClient(), "Suggest headphones under $200")  # someone else
        Conversation.objects.create(title="legacy", website_scope=[self.site])  # no owner

        response = self.owner.get("/api/conversations/")
        self.assertEqual(response.status_code, 200)
        rows = response.json()
        self.assertEqual([r["id"] for r in rows], [second["conversation_id"], first["conversation_id"]])
        self.assertEqual(set(rows[0]), {"id", "title", "website_scope", "updated_at"})
        self.assertEqual(rows[0]["website_scope"], [self.site])

    def test_list_without_session_is_empty_and_creates_no_session(self):
        response = APIClient().get("/api/conversations/")
        self.assertEqual(response.json(), [])
        self.assertNotIn("sessionid", response.cookies)

    def test_detail_shape_and_message_order(self):
        data = self.chat(self.owner, "Suggest headphones under $350")
        self.chat(self.owner, "only Sony", data["conversation_id"])
        response = self.owner.get(f"/api/conversations/{data['conversation_id']}/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(set(body), {"id", "title", "website_scope", "messages"})
        self.assertEqual([m["role"] for m in body["messages"]], ["user", "assistant", "user", "assistant"])
        self.assertEqual(body["messages"][0]["content"], "Suggest headphones under $350")
        self.assertEqual(set(body["messages"][0]), {"role", "content", "created_at"})
        self.assertNotIn("current_requirements", body)
        self.assertNotIn("owner_key", body)

    def test_other_owner_gets_404_not_403(self):
        data = self.chat(self.owner, "Suggest headphones under $350")
        stranger = APIClient()
        self.chat(stranger, "hello")  # the stranger has a session of their own
        response = stranger.get(f"/api/conversations/{data['conversation_id']}/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "conversation_not_found")
        self.assertEqual(APIClient().get(f"/api/conversations/{data['conversation_id']}/").status_code, 404)

    def test_unknown_id_is_404(self):
        self.chat(self.owner, "hello")
        self.assertEqual(self.owner.get("/api/conversations/999999/").status_code, 404)

    def test_ownerless_legacy_conversation_is_not_reachable(self):
        legacy = Conversation.objects.create(title="legacy", website_scope=[self.site])
        self.chat(self.owner, "hello")
        self.assertEqual(self.owner.get(f"/api/conversations/{legacy.id}/").status_code, 404)
