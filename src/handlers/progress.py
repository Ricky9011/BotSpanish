from aiogram import Router, F
from aiogram.fsm import state
from aiogram.types import Message
from aiogram.filters import Command

from src.services.user_service import UserService

router = Router(name="progress")


@router.message(Command("progreso"))
@router.message(F.text == "📊 Progreso")
@router.message(F.text == "📊 Mis estadísticas") # ¡Añade este!
async def cmd_progress(message: Message):
    await state.clear() # << AÑADIDO: Limpia el estado del usuario
    user_id = message.from_user.id
    stats = UserService.get_user_stats(user_id)

    if not stats:
        await message.answer("❌ No se encontraron datos de progreso.")
        return

    # Calcular porcentaje de completitud
    level_base = 50 if stats["level"] == "principiante" else 100 if stats["level"] == "intermedio" else 150
    percentage = min(100, int((stats["exercises"] / level_base) * 100))

    # Generar barra de progreso
    filled = '▓' * int(percentage / 5)
    empty = '░' * (20 - len(filled))
    progress_bar = f"{filled}{empty} {percentage}%"

    progress_text = (
        f"📈 **Tu Progreso**\n\n"
        f"📊 Nivel: {stats['level'].capitalize()}\n"
        f"✅ Ejercicios completados: {stats['exercises']}\n"
        f"🔥 Racha actual: {stats['streak_days']} días\n"
        f"👥 Amigos invitados: {stats['referrals']}\n"
        f"🏆 Puntos en retos: {stats['challenge_score']}\n\n"
        f"📊 Progreso del nivel:\n{progress_bar}"
    )
    if stats['last_practice']:
        progress_text += f"⏰ Última práctica: {stats['last_practice'].strftime('%Y-%m-%d %H:%M')}\n"

    await message.answer(progress_text)


@router.message(Command("logros"))
@router.message(F.text == "🎖️ Mis Logros")
async def cmd_achievements(message: Message):
    # Implementar lógica de logros
    await message.answer("🎖️ **Tus Logros**\n\nPróximamente...")