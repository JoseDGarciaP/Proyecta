from pydantic import BaseModel, ConfigDict, Field

from app.modules.parametros.models import ParaPlantilla, TipoMotivo


class MotivoEntrada(BaseModel):
    tipo: TipoMotivo
    nombre: str = Field(min_length=3, max_length=150)
    descripcion: str = Field(default="", max_length=500)
    requiere_comentario: bool = False
    activo: bool = True
    orden: int = 0


class MotivoSalida(MotivoEntrada):
    model_config = ConfigDict(from_attributes=True)
    id: int


class TipoAporteEntrada(BaseModel):
    nombre: str = Field(min_length=3, max_length=120)
    descripcion: str = Field(default="", max_length=500)
    activo: bool = True
    orden: int = 0


class TipoAporteSalida(TipoAporteEntrada):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PlantillaEntrada(BaseModel):
    titulo: str = Field(min_length=3, max_length=120)
    texto: str = Field(min_length=5, max_length=2000)
    para: ParaPlantilla = ParaPlantilla.TODOS
    activo: bool = True
    orden: int = 0


class PlantillaSalida(PlantillaEntrada):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ParametrosColaboracion(BaseModel):
    """Lo que necesitan los formularios de colaboración: solo lo activo, en orden."""

    motivos: list[MotivoSalida]
    tipos_aporte: list[TipoAporteSalida]
    plantillas: list[PlantillaSalida]
