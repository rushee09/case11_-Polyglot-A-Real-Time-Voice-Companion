from fastapi import APIRouter
from app.services import asr_service, llm_service, storage_service
from app.models.schemas import HealthResponse
from app.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    lm_ok = await llm_service.check_lm_studio()
    asr_ok = asr_service.is_asr_available()
    storage = storage_service.get_storage_mode()
    return HealthResponse(
        status="ok",
        lm_studio="connected" if lm_ok else "unavailable (fallback mode active)",
        asr="available" if asr_ok else "unavailable (install faster-whisper)",
        storage_mode=storage,
        whisper_model=settings.whisper_model,
        lm_model=settings.lm_studio_model,
    )
