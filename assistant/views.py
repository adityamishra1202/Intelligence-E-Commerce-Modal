import logging

from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from websites.models import Website
from conversations.models import Conversation, Message

from assistant.serializers import ChatRequestSerializer

from assistant.services.requirements_service import RequirementsService
from assistant.services.hybrid_search_service import HybridSearchService
from assistant.services.grounded_response_service import GroundedResponseService


logger = logging.getLogger(__name__)


class ChatAPIView(APIView):

    def get_or_create_conversation(self, conversation_id, website_ids):

        # Create a new conversation when no conversation ID is supplied.
        if conversation_id is None:
            return Conversation.objects.create(
                title="New conversation",
                website_scope=website_ids,
                current_requirements={},
            )

        # Retrieve an existing conversation.
        conversation = Conversation.objects.filter(
            id=conversation_id
        ).first()

        if conversation is None:
            return None

        # Ensure the requested websites match the conversation scope.
        if sorted(conversation.website_scope) != sorted(website_ids):
            return None

        return conversation

    def post(self, request):

        # --------------------------------------------------
        # 1. Validate the incoming request.
        # --------------------------------------------------

        serializer = ChatRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "error": "Invalid request.",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        message = serializer.validated_data["message"]

        website_ids = sorted(
            set(serializer.validated_data["website_ids"])
        )

        conversation_id = serializer.validated_data.get(
            "conversation_id"
        )

        # --------------------------------------------------
        # 2. Verify that all requested websites exist and
        #    are active.
        # --------------------------------------------------

        websites = Website.objects.filter(
            id__in=website_ids,
            is_active=True,
        )

        if websites.count() != len(website_ids):
            return Response(
                {
                    "error": (
                        "One or more requested websites do not "
                        "exist or are inactive."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------
        # 3. Retrieve or create the conversation.
        # --------------------------------------------------

        conversation = self.get_or_create_conversation(
            conversation_id=conversation_id,
            website_ids=website_ids,
        )

        if conversation is None:
            return Response(
                {
                    "error": (
                        "Conversation not found or website scope "
                        "does not match."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:

            with transaction.atomic():

                # --------------------------------------------------
                # 4. Load previous messages before saving the
                #    current message.
                # --------------------------------------------------

                conversation_history = list(
                    conversation.messages.order_by(
                        "created_at",
                        "id",
                    ).values(
                        "role",
                        "content",
                    )
                )[-10:]

                # --------------------------------------------------
                # 5. Save the user's current message.
                # --------------------------------------------------

                Message.objects.create(
                    conversation=conversation,
                    role="user",
                    content=message,
                )

                # --------------------------------------------------
                # 6. Extract shopping requirements using the
                #    current message and conversation history.
                # --------------------------------------------------

                requirements_service = RequirementsService()

                requirements = requirements_service.extract(
                    user_message=message,
                    conversation_history=conversation_history,
                )

                # --------------------------------------------------
                # 7. Merge requirements with existing shopping
                #    preferences when applicable.
                # --------------------------------------------------

                if conversation.current_requirements:

                    requirements = (
                        requirements_service.merge_requirements(
                            previous_requirements=(
                                conversation.current_requirements
                            ),
                            new_requirements=requirements,
                            user_message=message,
                        )
                    )

                # --------------------------------------------------
                # 8. Handle general questions.
                # --------------------------------------------------

                if requirements.intent == "general_question":

                    answer = (
                        "I'm EcommerceAI, your shopping assistant. "
                        "Ask me to find or compare products, and "
                        "I'll search the selected product catalog."
                    )

                    products = []

                # --------------------------------------------------
                # 9. Handle unclear shopping requests.
                # --------------------------------------------------

                elif requirements.intent == "clarification_needed":

                    answer = (
                        "Could you clarify what kind of product "
                        "you're looking for?"
                    )

                    products = []

                # --------------------------------------------------
                # 10. Search products using hybrid retrieval and
                #     generate a grounded answer.
                # --------------------------------------------------

                else:

                    hybrid_search_service = HybridSearchService()

                    products = hybrid_search_service.search(
                        requirements=requirements,
                        website_ids=website_ids,
                        limit=20,
                    )

                    response_service = GroundedResponseService()

                    answer = response_service.generate_answer(
                        user_message=message,
                        products=products,
                    )

                # --------------------------------------------------
                # 11. Save the assistant's response.
                # --------------------------------------------------

                Message.objects.create(
                    conversation=conversation,
                    role="assistant",
                    content=answer,
                )

                # --------------------------------------------------
                # 12. Update shopping memory only when the user
                #     makes a shopping-related request.
                # --------------------------------------------------

                if requirements.intent in [
                    "product_search",
                    "product_comparison",
                ]:

                    conversation.current_requirements = (
                        requirements.model_dump(mode="json")
                    )

                # Set the conversation title from the first message.
                if conversation.title == "New conversation":
                    conversation.title = message[:200]

                # Save the conversation.
                conversation.save(
                    update_fields=[
                        "title",
                        "current_requirements",
                        "updated_at",
                    ]
                )

                # --------------------------------------------------
                # 13. Return the response for the frontend.
                # --------------------------------------------------

                return Response(
                    {
                        "conversation_id": conversation.id,
                        "message": message,
                        "intent": requirements.intent,
                        "answer": answer,
                        "requirements": requirements.model_dump(),
                        "total_products": len(products),
                        "products": products,
                    },
                    status=status.HTTP_200_OK,
                )

        except ValueError as exc:

            logger.warning(
                "Invalid EcommerceAI chat request: %s",
                str(exc),
            )

            return Response(
                {
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:

            logger.exception(
                "Unexpected error while processing EcommerceAI chat request."
            )

            return Response(
                {
                    "error": (
                        "EcommerceAI could not process your request. "
                        "Please try again."
                    )
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )