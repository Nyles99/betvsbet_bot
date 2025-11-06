# utils/scoring_system.py

def calculate_points(predicted_score: str, actual_score: str) -> int:
    """
    Расчет очков за ставку по системе:
    - Угадал точный счет: 4 очка
    - Угадал исход и разницу: 2 очка  
    - Угадал исход (победа/ничья): 1 очко
    - Не угадал: 0 очков
    
    Args:
        predicted_score: Ставка пользователя в формате "X-Y"
        actual_score: Реальный счет в формате "X-Y"
    
    Returns:
        int: Количество начисленных очков
    """
    if not predicted_score or not actual_score:
        return 0
    
    try:
        pred_home, pred_away = map(int, predicted_score.split('-'))
        actual_home, actual_away = map(int, actual_score.split('-'))
        
        # Угадал точный счет
        if pred_home == actual_home and pred_away == actual_away:
            return 4
        
        # Определяем исходы
        pred_outcome = _get_match_outcome(pred_home, pred_away)
        actual_outcome = _get_match_outcome(actual_home, actual_away)
        
        # Угадал ничью
        if pred_outcome == 'draw' and actual_outcome == 'draw':
            return 2
        
        # Угадал исход (победа/поражение)
        if pred_outcome == actual_outcome:
            # Проверяем разницу голов
            pred_diff = pred_home - pred_away
            actual_diff = actual_home - actual_away
            
            # Угадал исход и разницу
            if pred_diff == actual_diff:
                return 2
            # Угадал только исход
            else:
                return 1
        
        # Не угадал
        return 0
        
    except (ValueError, AttributeError):
        return 0

def _get_match_outcome(home_goals: int, away_goals: int) -> str:
    """Определяет исход матча"""
    if home_goals > away_goals:
        return 'home_win'
    elif home_goals < away_goals:
        return 'away_win'
    else:
        return 'draw'

def get_scoring_rules_description() -> str:
    """Возвращает описание системы подсчета очков"""
    return """
🎯 **Система подсчета очков:**

✅ **4 очка** - За точное угадывание счета матча
✅ **2 очка** - За угадывание исхода матча и разницы голов
✅ **2 очка** - За угадывание ничейного результата  
✅ **1 очко** - За угадывание исхода матча (победа/поражение)
❌ **0 очков** - Если исход не угадан

📝 **Примеры:**
- Реальный счет: 2-1
  • Ставка 2-1 = 4 очка
  • Ставка 3-2 = 2 очка (исход + разница)
  • Ставка 1-0 = 1 очко (только исход)
  • Ставка 2-2 = 0 очков

- Реальный счет: 1-1  
  • Ставка 1-1 = 4 очка
  • Ставка 2-2 = 2 очка (ничья)
  • Ставка 2-1 = 0 очков
"""