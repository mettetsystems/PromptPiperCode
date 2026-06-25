from fastapi import APIRouter, Depends
from fastapi.responses import Response

from prompt_piper_api.config import Settings, get_settings
from prompt_piper_api.schemas.registry import (
    RegistryPromptDetail,
    RegistryPromptSummary,
    to_registry_summary,
)
from prompt_piper_api.services.exceptions import PromptNotFoundError
from prompt_piper_api.services.registry_browse_service import RegistryBrowseService

router = APIRouter(prefix="/registry", tags=["registry"])

_browse_service: RegistryBrowseService | None = None


def get_registry_browse_service(
    settings: Settings = Depends(get_settings),
) -> RegistryBrowseService:
    global _browse_service
    if _browse_service is None or _browse_service.registry.registry_path != settings.registry_path:
        _browse_service = RegistryBrowseService(
            settings.registry_path,
            settings.artifacts_path,
        )
    return _browse_service


@router.get("/prompts", response_model=list[RegistryPromptSummary])
def list_registry_prompts(
    service: RegistryBrowseService = Depends(get_registry_browse_service),
) -> list[RegistryPromptSummary]:
    return [to_registry_summary(item) for item in service.registry.list_prompts()]


@router.get("/prompts/{prompt_id}", response_model=RegistryPromptDetail)
def get_registry_prompt(
    prompt_id: str,
    service: RegistryBrowseService = Depends(get_registry_browse_service),
) -> RegistryPromptDetail:
    detail = service.get_prompt_detail(prompt_id)
    if detail is None:
        raise PromptNotFoundError(prompt_id)
    return detail


@router.get("/prompts/{prompt_id}/artifacts/{filename}")
def get_artifact_file(
    prompt_id: str,
    filename: str,
    service: RegistryBrowseService = Depends(get_registry_browse_service),
) -> Response:
    if filename.endswith(".pdf"):
        pdf_payload = service.read_artifact_bytes(prompt_id, filename)
        if pdf_payload is None:
            raise PromptNotFoundError(prompt_id)
        pdf_content, pdf_media_type = pdf_payload
        return Response(content=pdf_content, media_type=pdf_media_type)

    text_payload = service.read_artifact_file(prompt_id, filename)
    if text_payload is None:
        raise PromptNotFoundError(prompt_id)
    text_content, text_media_type = text_payload
    return Response(content=text_content, media_type=text_media_type)
