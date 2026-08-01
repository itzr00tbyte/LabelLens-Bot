import pytest
from app.database.models import SubmissionStatus
from app.database.repositories import UserRepository
from app.services.submission_service import SubmissionService


@pytest.mark.asyncio
async def test_valid_state_transitions(async_session):
    user_repo = UserRepository(async_session)
    user = await user_repo.get_or_create(telegram_id=12345, username="testuser")

    service = SubmissionService(async_session)
    sub = await service.sub_repo.create(
        user_id=user.id,
        telegram_file_id="tg_file_123",
        original_filename="sample.jpg",
    )
    assert sub.status == SubmissionStatus.UPLOADED

    # Uploaded -> Processing
    await service._transition_status(sub, SubmissionStatus.PROCESSING, "Processing start")
    assert sub.status == SubmissionStatus.PROCESSING

    # Processing -> Matched
    await service._transition_status(sub, SubmissionStatus.MATCHED, "Matched template")
    assert sub.status == SubmissionStatus.MATCHED

    # Matched -> Approved
    approved_sub = await service.approve_submission(sub.id, user.id)
    assert approved_sub.status == SubmissionStatus.APPROVED


@pytest.mark.asyncio
async def test_invalid_state_transition(async_session):
    user_repo = UserRepository(async_session)
    user = await user_repo.get_or_create(telegram_id=12345, username="testuser")

    service = SubmissionService(async_session)
    sub = await service.sub_repo.create(
        user_id=user.id,
        telegram_file_id="tg_file_123",
    )

    # Invalid transition: UPLOADED -> APPROVED directly
    with pytest.raises(ValueError, match="Invalid state transition"):
        await service._transition_status(sub, SubmissionStatus.APPROVED, "Direct approve invalid")
