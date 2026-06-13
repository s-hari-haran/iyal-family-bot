import datetime
import sqlite3
import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from backend.database import supabase_client, is_local_mode, SQLITE_PATH

logger = logging.getLogger("uvicorn")
router = APIRouter(prefix="/api/insights", tags=["Background Insight Engine"])

@router.post("/generate/{family_id}")
async def generate_family_insights(family_id: str):
    """
    Background Insight Engine trigger.
    Analyzes family memory (expenses, budgets, debts, goals) and creates savings insights.
    """
    generated_count = 0
    today = datetime.date.today()
    start_of_month = today.replace(day=1).isoformat()
    now_str = datetime.datetime.now().isoformat()

    if not is_local_mode:
        # --- Supabase Mode ---
        # 1. Budgets vs Expenses
        try:
            budgets_res = supabase_client.table("budgets").select("category, monthly_limit").eq("family_id", family_id).execute()
            for budget in budgets_res.data:
                category = budget["category"]
                limit = float(budget["monthly_limit"])
                
                expenses_res = supabase_client.table("expenses").select("amount").eq("family_id", family_id).eq("category", category).eq("status", "confirmed").gte("date", start_of_month).execute()
                spent = sum(float(exp["amount"]) for exp in expenses_res.data)
                
                if limit > 0:
                    percent = (spent / limit) * 100
                    if percent >= 95:
                        title = f"Critical Overspending in {category.capitalize()}"
                        desc = f"You have spent ₹{spent:.0f} of your ₹{limit:.0f} monthly limit for {category} ({percent:.0f}% used)."
                        
                        existing = supabase_client.table("insights").select("id").eq("family_id", family_id).eq("title", title).gte("created_at", today.isoformat()).execute()
                        if not existing.data:
                            supabase_client.table("insights").insert({
                                "family_id": family_id,
                                "title": title,
                                "description": desc,
                                "insight_type": "overspending"
                            }).execute()
                            generated_count += 1
                    elif percent >= 80:
                        title = f"Approaching {category.capitalize()} Budget Limit"
                        desc = f"You have spent ₹{spent:.0f} of your ₹{limit:.0f} monthly limit for {category} ({percent:.0f}% used)."
                        
                        existing = supabase_client.table("insights").select("id").eq("family_id", family_id).eq("title", title).gte("created_at", today.isoformat()).execute()
                        if not existing.data:
                            supabase_client.table("insights").insert({
                                "family_id": family_id,
                                "title": title,
                                "description": desc,
                                "insight_type": "overspending"
                            }).execute()
                            generated_count += 1
        except Exception as e:
            logger.error(f"Error computing live insights: {e}")

        # 2. Check Goals
        try:
            goals_res = supabase_client.table("goals").select("id, goal_name, target_amount, current_amount, target_date").eq("family_id", family_id).execute()
            for goal in goals_res.data:
                name = goal["goal_name"]
                target = float(goal["target_amount"])
                current = float(goal["current_amount"])
                target_date = datetime.date.fromisoformat(goal["target_date"])
                
                days_left = (target_date - today).days
                if current < target and 0 < days_left <= 30:
                    percent = (current / target) * 100
                    title = f"Milestone Reminder: {name}"
                    desc = f"Your goal '{name}' target date is in {days_left} days. You are currently at ₹{current:.0f} of ₹{target:.0f} ({percent:.0f}% complete)."
                    
                    existing = supabase_client.table("insights").select("id").eq("family_id", family_id).eq("title", title).gte("created_at", today.isoformat()).execute()
                    if not existing.data:
                        supabase_client.table("insights").insert({
                            "family_id": family_id,
                            "title": title,
                            "description": desc,
                            "insight_type": "delayed_goal"
                        }).execute()
                        generated_count += 1
        except Exception as e:
            pass

        # 3. Check Debts
        try:
            debts_res = supabase_client.table("debts").select("id, lender_name, borrower_name, amount, due_date").eq("family_id", family_id).eq("status", "active").execute()
            for debt in debts_res.data:
                lender = debt["lender_name"]
                borrower = debt["borrower_name"]
                amount = float(debt["amount"])
                
                if debt["due_date"]:
                    due_date = datetime.date.fromisoformat(debt["due_date"])
                    days_left = (due_date - today).days
                    
                    if days_left <= 7:
                        title = "Upcoming Loan Repayment Due"
                        if days_left < 0:
                            desc = f"The loan of ₹{amount:.0f} from {lender} to {borrower} is overdue by {abs(days_left)} days."
                        elif days_left == 0:
                            desc = f"The loan of ₹{amount:.0f} from {lender} to {borrower} is due today."
                        else:
                            desc = f"The loan of ₹{amount:.0f} from {lender} to {borrower} is due in {days_left} days."
                            
                        existing = supabase_client.table("insights").select("id").eq("family_id", family_id).eq("title", f"{title}: {lender}").gte("created_at", today.isoformat()).execute()
                        if not existing.data:
                            supabase_client.table("insights").insert({
                                "family_id": family_id,
                                "title": f"{title}: {lender}",
                                "description": desc,
                                "insight_type": "debt_risk"
                            }).execute()
                            generated_count += 1
        except Exception as e:
            pass

        # 4. Savings Nudges
        try:
            nudges = [
                {
                    "title": "Low-Risk Savings Tip: PPF Advantage",
                    "description": "Public Provident Fund (PPF) is government-backed and tax-free. Contributing even ₹1,000 monthly can grow into a substantial tax-free corpus due to compound interest.",
                    "insight_type": "savings_nudge"
                },
                {
                    "title": "Build an Emergency Buffer",
                    "description": "Consider setting aside 3 months of groceries budget in a Sweep-in Fixed Deposit. This is highly liquid and earns higher interest than a savings account.",
                    "insight_type": "savings_nudge"
                }
            ]
            for nudge in nudges:
                existing = supabase_client.table("insights").select("id").eq("family_id", family_id).eq("title", nudge["title"]).execute()
                if not existing.data:
                    supabase_client.table("insights").insert({
                        "family_id": family_id,
                        "title": nudge["title"],
                        "description": nudge["description"],
                        "insight_type": nudge["insight_type"]
                    }).execute()
                    generated_count += 1
        except Exception as e:
            pass

        # Return live insights
        all_insights = supabase_client.table("insights").select("*").eq("family_id", family_id).order("created_at", desc=True).limit(10).execute()
        return {
            "status": "success",
            "new_insights_generated": generated_count,
            "insights": all_insights.data
        }
    else:
        # --- Local SQLite Mode ---
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Budgets vs Expenses
        try:
            cursor.execute("SELECT category, monthly_limit FROM budgets WHERE family_id = ?", (family_id,))
            budgets = cursor.fetchall()
            for budget in budgets:
                category = budget["category"]
                limit = float(budget["monthly_limit"])
                
                cursor.execute(
                    "SELECT amount FROM expenses WHERE family_id = ? AND category = ? AND status = 'confirmed' AND date >= ?",
                    (family_id, category, start_of_month)
                )
                spent = sum(float(r[0]) for r in cursor.fetchall())
                
                if limit > 0:
                    percent = (spent / limit) * 100
                    if percent >= 95:
                        title = f"Critical Overspending in {category.capitalize()}"
                        desc = f"You have spent ₹{spent:.0f} of your ₹{limit:.0f} monthly limit for {category} ({percent:.0f}% used)."
                        
                        cursor.execute("SELECT id FROM insights WHERE family_id = ? AND title = ? AND created_at >= ?", (family_id, title, today.isoformat()))
                        if not cursor.fetchone():
                            new_ins_id = f"ins-{datetime.datetime.now().timestamp()}"
                            cursor.execute(
                                "INSERT INTO insights (id, family_id, title, description, insight_type, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                (new_ins_id, family_id, title, desc, "overspending", now_str)
                            )
                            generated_count += 1
                    elif percent >= 80:
                        title = f"Approaching {category.capitalize()} Budget Limit"
                        desc = f"You have spent ₹{spent:.0f} of your ₹{limit:.0f} monthly limit for {category} ({percent:.0f}% used)."
                        
                        cursor.execute("SELECT id FROM insights WHERE family_id = ? AND title = ? AND created_at >= ?", (family_id, title, today.isoformat()))
                        if not cursor.fetchone():
                            new_ins_id = f"ins-{datetime.datetime.now().timestamp()}"
                            cursor.execute(
                                "INSERT INTO insights (id, family_id, title, description, insight_type, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                (new_ins_id, family_id, title, desc, "overspending", now_str)
                            )
                            generated_count += 1
            conn.commit()
        except Exception as e:
            logger.error(f"Error computing local budget insights: {e}")

        # 2. Check Goals
        try:
            cursor.execute("SELECT id, goal_name, target_amount, current_amount, target_date FROM goals WHERE family_id = ?", (family_id,))
            goals = cursor.fetchall()
            for goal in goals:
                name = goal["goal_name"]
                target = float(goal["target_amount"])
                current = float(goal["current_amount"])
                target_date = datetime.date.fromisoformat(goal["target_date"])
                
                days_left = (target_date - today).days
                if current < target and 0 < days_left <= 30:
                    percent = (current / target) * 100
                    title = f"Milestone Reminder: {name}"
                    desc = f"Your goal '{name}' target date is in {days_left} days. You are currently at ₹{current:.0f} of ₹{target:.0f} ({percent:.0f}% complete)."
                    
                    cursor.execute("SELECT id FROM insights WHERE family_id = ? AND title = ? AND created_at >= ?", (family_id, title, today.isoformat()))
                    if not cursor.fetchone():
                        new_ins_id = f"ins-{datetime.datetime.now().timestamp()}"
                        cursor.execute(
                            "INSERT INTO insights (id, family_id, title, description, insight_type, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                            (new_ins_id, family_id, title, desc, "delayed_goal", now_str)
                        )
                        generated_count += 1
            conn.commit()
        except Exception as e:
            pass

        # 3. Check Debts
        try:
            cursor.execute("SELECT id, lender_name, borrower_name, amount, due_date FROM debts WHERE family_id = ? AND status = 'active'", (family_id,))
            debts = cursor.fetchall()
            for debt in debts:
                lender = debt["lender_name"]
                borrower = debt["borrower_name"]
                amount = float(debt["amount"])
                
                if debt["due_date"]:
                    due_date = datetime.date.fromisoformat(debt["due_date"])
                    days_left = (due_date - today).days
                    
                    if days_left <= 7:
                        title = "Upcoming Loan Repayment Due"
                        if days_left < 0:
                            desc = f"The loan of ₹{amount:.0f} from {lender} to {borrower} is overdue by {abs(days_left)} days."
                        elif days_left == 0:
                            desc = f"The loan of ₹{amount:.0f} from {lender} to {borrower} is due today."
                        else:
                            desc = f"The loan of ₹{amount:.0f} from {lender} to {borrower} is due in {days_left} days."
                            
                        cursor.execute("SELECT id FROM insights WHERE family_id = ? AND title = ? AND created_at >= ?", (family_id, f"{title}: {lender}", today.isoformat()))
                        if not cursor.fetchone():
                            new_ins_id = f"ins-{datetime.datetime.now().timestamp()}"
                            cursor.execute(
                                "INSERT INTO insights (id, family_id, title, description, insight_type, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                (new_ins_id, family_id, f"{title}: {lender}", desc, "debt_risk", now_str)
                            )
                            generated_count += 1
            conn.commit()
        except Exception as e:
            pass

        # 4. Savings Nudges
        try:
            nudges = [
                {
                    "title": "Low-Risk Savings Tip: PPF Advantage",
                    "description": "Public Provident Fund (PPF) is government-backed and tax-free. Contributing even ₹1,000 monthly can grow into a substantial tax-free corpus due to compound interest.",
                    "insight_type": "savings_nudge"
                },
                {
                    "title": "Build an Emergency Buffer",
                    "description": "Consider setting aside 3 months of groceries budget in a Sweep-in Fixed Deposit. This is highly liquid and earns higher interest than a savings account.",
                    "insight_type": "savings_nudge"
                }
            ]
            for nudge in nudges:
                cursor.execute("SELECT id FROM insights WHERE family_id = ? AND title = ?", (family_id, nudge["title"]))
                if not cursor.fetchone():
                    new_ins_id = f"ins-{datetime.datetime.now().timestamp()}"
                    cursor.execute(
                        "INSERT INTO insights (id, family_id, title, description, insight_type, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (new_ins_id, family_id, nudge["title"], nudge["description"], nudge["insight_type"], now_str)
                    )
                    generated_count += 1
            conn.commit()
        except Exception as e:
            pass

        # Query all insights back
        cursor.execute("SELECT * FROM insights WHERE family_id = ? ORDER BY created_at DESC LIMIT 10", (family_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return {
            "status": "success",
            "new_insights_generated": generated_count,
            "insights": rows
        }
