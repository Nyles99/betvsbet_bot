if current_players:
            text = f"🏆 **Рейтинг игроков: {tournament[1]}**\n\n"
            text += "```\n"
            text += "Место| Логин        | Матчи | ТС |Очки\n"
            text += "-----|--------------|-------|----|----\n"
            
            for i, player in enumerate(current_players, start_index + 1):
                # Определяем медаль для первых трех мест
                medal = ""
                if i == 1:
                    medal = "🥇"
                elif i == 2:
                    medal = "🥈"
                elif i == 3:
                    medal = "🥉"
                else:
                    medal = f"{i}"
                
                # Форматируем логин (обрезаем если длинный)
                username = player['username']
                if len(username) > 12:
                    username = username[:12] + "..."
                else:
                    username = username.ljust(12)
                
                # Форматируем количество матчей
                matches_text = f"{player['matches_played']}"
                if player['matches_played'] == 1:
                    matches_text += " матч"
                elif 2 <= player['matches_played'] <= 4:
                    matches_text += " матча"
                else:
                    matches_text += " матчей"
                
                text += f"{medal:3} | {username} | {matches_text:3}|{player['exact_scores']:3} |{player['total_points']:3}\n"
            
            text += "```\n\n"
            text += f"📊 Всего игроков: {total_players}\n"
            text += f"📄 Страница {page + 1}/{(total_players + players_per_page - 1) // players_per_page}"
            
            await safe_edit_message(
                callback,
                text,
                get_tournament_leaderboard_keyboard(tournament_id, page, total_players, players_per_page)
            )
        else:
            text = f"🏆 **Рейтинг игроков: {tournament[1]}**\n\n"
            text += "📊 В этом турнире пока нет результатов для составления рейтинга.\n\n"
            text += "Рейтинг появится после того как администратор введет результаты матчей."
            
            await safe_edit_message(
                callback,
                text,
                get_tournament_detail_keyboard(tournament_id)
            )