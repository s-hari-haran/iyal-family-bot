"use client";

import React, { useState, useEffect } from "react";
import { 
  Home, 
  List, 
  Mic, 
  Sparkles, 
  Users, 
  Search, 
  Plus, 
  Trash2, 
  Edit2, 
  Check, 
  X, 
  ShieldAlert, 
  Award, 
  AlertTriangle, 
  Info, 
  ArrowRight, 
  ArrowLeft, 
  Volume2, 
  Globe2, 
  ShoppingCart, 
  Zap, 
  Fuel, 
  GraduationCap, 
  Folder, 
  Wallet, 
  TrendingDown, 
  TrendingUp, 
  Percent, 
  Lock, 
  PhoneCall,
  Send,
  Pencil,
  Info
} from "lucide-react";

// Autoritative Mock Fallback Data representing family memory when database is cleared
const MOCK_FAMILY_ID = "f8e56bdf-99a3-4813-8b77-3e5f7b88939c";
const MOCK_MEMBER_ID = "m1234567-89ab-cdef-0123-456789abcdef";

const MOCK_STATS = {
  total_assets: 0.00,      // Cleared start state
  total_debts: 0.00,       // Cleared start state
  savings_rate: 0.0,
  health_score: 100        // Healthy baseline
};

const MOCK_BUDGETS = [
  { category: "groceries", limit: 10000.00, spent: 0.00, remaining: 10000.00 },
  { category: "utilities", limit: 5000.00, spent: 0.00, remaining: 5000.00 },
  { category: "fuel", limit: 4000.00, spent: 0.00, remaining: 4000.00 },
  { category: "tuition", limit: 12000.00, spent: 0.00, remaining: 12000.00 }
];

const MOCK_PENDING_LOW: any[] = [];
const MOCK_PENDING_MED: any[] = [];
const MOCK_TIMELINE: any[] = [];
const MOCK_INSIGHTS: any[] = [];
const INITIAL_MOCK_TRANSACTIONS: any[] = [];

const CATEGORY_ICONS: Record<string, any> = {
  groceries: ShoppingCart,
  utilities: Zap,
  fuel: Fuel,
  tuition: GraduationCap,
  debt: TrendingDown,
  misc: Folder
};

export default function ConsumerDashboard() {
  // Navigation Router state
  const [activeTab, setActiveTab] = useState<"overview" | "ledger" | "budgets" | "debts" | "assistant" | "voice_logs" | "profiles">("overview");

  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  // Core data states
  const [stats, setStats] = useState(MOCK_STATS);
  const [budgets, setBudgets] = useState(MOCK_BUDGETS);
  const [pendingLow, setPendingLow] = useState<any[]>(MOCK_PENDING_LOW);
  const [pendingMed, setPendingMed] = useState<any[]>(MOCK_PENDING_MED);
  const [timeline, setTimeline] = useState<any[]>(MOCK_TIMELINE);
  const [insights, setInsights] = useState<any[]>(MOCK_INSIGHTS);
  const [transactions, setTransactions] = useState<any[]>(INITIAL_MOCK_TRANSACTIONS);

  // Connection and Family states
  const [isOffline, setIsOffline] = useState(true);
  const [selectedFamily, setSelectedFamily] = useState(MOCK_FAMILY_ID);

  // Edit states for trust layer review
  const [editRequestValues, setEditRequestValues] = useState<Record<string, any>>({});

  // Simulator / Chat Assistant State
  const [simText, setSimText] = useState("");
  const [simSpeaker, setSimSpeaker] = useState("Ramesh");
  const [simLanguage, setSimLanguage] = useState("en");
  const [agentState, setAgentState] = useState<"Thinking" | "Executing Tool" | "Updating Memory" | "Idle">("Idle");
  
  const [simLogs, setSimLogs] = useState<Array<{ sender: "user" | "assistant"; text: string }>>([
    { sender: "assistant", text: "Hello! Welcome back to your family money memory. Who is speaking today, and how can I help you?" }
  ]);
  const [simLoading, setSimLoading] = useState(false);

  // Voice history log (Technical logs excluded)
  const [voiceHistory, setVoiceHistory] = useState<Array<{ member: string; text: string; action: string; time: string }>>([]);

  // Family members list
  const [members, setMembers] = useState<Array<{ id?: string, name: string, role: string, phone_number?: string, language: string, voice: boolean }>>([
    { id: "m1", name: "Ramesh", role: "Father", phone_number: "+919449694564", language: "English", voice: true },
    { id: "m2", name: "Sunita", role: "Mother", phone_number: "+919538133265", language: "Hindi", voice: true },
    { id: "m3", name: "Hari", role: "Son", phone_number: "+919538133265", language: "English", voice: false },
    { id: "m4", name: "Prakash", role: "Brother", phone_number: "+917760599655", language: "English", voice: true }
  ]);
  const [familyName, setFamilyName] = useState<string>("Sharma Family");

  // Goals
  const [goals, setGoals] = useState<Array<{ id?: string; name: string; current: number; target: number; target_date?: string; est: string }>>([
    { name: "Emergency Fund", current: 0, target: 100000, target_date: "2026-10-31", est: "Target: Oct 2026" },
    { name: "Education Fund", current: 0, target: 150000, target_date: "2027-06-30", est: "Target: Jun 2027" },
    { name: "Vacation Savings", current: 0, target: 80000, target_date: "2026-12-31", est: "Target: Dec 2026" },
    { name: "Vehicle Goal", current: 0, target: 200000, target_date: "2028-03-31", est: "Target: Mar 2028" }
  ]);

  // Budget editing states
  const [editingBudgetId, setEditingBudgetId] = useState<string | null>(null);
  const [editingBudgetLimit, setEditingBudgetLimit] = useState<number>(0);
  const [isAddBudgetOpen, setIsAddBudgetOpen] = useState(false);
  const [newBudgetCategory, setNewBudgetCategory] = useState("");
  const [newBudgetLimit, setNewBudgetLimit] = useState<number>(0);

  // Goal editing states
  const [editingGoalId, setEditingGoalId] = useState<string | null>(null);
  const [editingGoalData, setEditingGoalData] = useState<{ goal_name: string; target_amount: number; target_date: string }>({ goal_name: "", target_amount: 0, target_date: "" });
  const [isAddGoalOpen, setIsAddGoalOpen] = useState(false);
  const [newGoalName, setNewGoalName] = useState("");
  const [newGoalTarget, setNewGoalTarget] = useState<number>(0);
  const [newGoalDate, setNewGoalDate] = useState("");

  // Family name editing
  const [isEditingFamilyName, setIsEditingFamilyName] = useState(false);
  const [editFamilyNameValue, setEditFamilyNameValue] = useState("");

  // Activity Feed Filters & Expansion States
  const [feedFilterMember, setFeedFilterMember] = useState<string>("All");
  const [feedFilterType, setFeedFilterType] = useState<string>("All");
  const [expandedActivityId, setExpandedActivityId] = useState<string | null>(null);

  // Ledger Sorting & Grouping States
  const [sortBy, setSortBy] = useState<"date-desc" | "date-asc" | "amount-desc" | "amount-asc">("date-desc");
  const [groupByCategory, setGroupByCategory] = useState<boolean>(false);

  // Modals Visibility
  const [isAddTransactionOpen, setIsAddTransactionOpen] = useState(false);
  const [addTxType, setAddTxType] = useState<"expense" | "debt">("expense");
  const [isAddExpenseOpen, setIsAddExpenseOpen] = useState(false);
  const [isAddDebtOpen, setIsAddDebtOpen] = useState(false);
  const [isEditMemberOpen, setIsEditMemberOpen] = useState(false);
  const [editingMember, setEditingMember] = useState<any>(null);
  
  // Modal Fields states
  const [expAmount, setExpAmount] = useState<number>(0);
  const [expCategory, setExpCategory] = useState<string>("groceries");
  const [expDesc, setExpDesc] = useState<string>("");
  const [expSpeaker, setExpSpeaker] = useState<string>("Hari");

  const [debtAmount, setDebtAmount] = useState<number>(0);
  const [debtLender, setDebtLender] = useState<string>("Sharma Family");
  const [debtBorrower, setDebtBorrower] = useState<string>("Uncle Vinay");
  const [debtDueDate, setDebtDueDate] = useState<string>("2026-07-15");
  const [debtNote, setDebtNote] = useState<string>("");
  const [debtSpeaker, setDebtSpeaker] = useState<string>("Ramesh");

  const [memberLang, setMemberLang] = useState<string>("English");
  const [memberRole, setMemberRole] = useState<string>("Son");
  const [memberVoice, setMemberVoice] = useState<boolean>(true);
  const [memberPhone, setMemberPhone] = useState<string>("");

  // States for Editing an existing transaction
  const [editingTransaction, setEditingTransaction] = useState<any>(null);
  const [editTxAmount, setEditTxAmount] = useState<number>(0);
  const [editTxCategory, setEditTxCategory] = useState<string>("groceries");
  const [editTxDesc, setEditTxDesc] = useState<string>("");
  const [editTxLender, setEditTxLender] = useState<string>("");
  const [editTxBorrower, setEditTxBorrower] = useState<string>("");

  // Filters state for Transactions tab
  const [filterMember, setFilterMember] = useState<string>("All");
  const [filterCategory, setFilterCategory] = useState<string>("All");
  const [filterType, setFilterType] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

  // Auto-scroll chat to bottom
  useEffect(() => {
    const chatContainer = document.querySelector(".assistant-chat-transcript");
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }, [simLogs]);

  // Outbound call handler for testing the real telephony agent
  const triggerOutboundCall = async (phone: string, name: string) => {
    try {
      const res = await fetch(`${API_BASE}/trust/trigger-call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: phone, member_name: name })
      });
      if (res.ok) {
        alert(`Request successful! Ringing physical phone line ${phone} for ${name}...`);
      } else {
        const err = await res.json();
        alert(`Outbound call failed: ${err.detail || "Error initiating call"}`);
      }
    } catch (e) {
      alert("Could not connect to FastAPI server to trigger call.");
    }
  };

  const loadData = async (familyId: string) => {
    try {
      const summaryRes = await fetch(`${API_BASE}/trust/summary/${familyId}`);
      let summaryData: any = {};
      if (summaryRes.ok) {
        const sData = await summaryRes.json();
        summaryData = sData;
        setStats({
          total_assets: sData.total_assets || 0,
          total_debts: sData.total_debts || 0,
          savings_rate: sData.savings_rate || 0,
          health_score: sData.health_score || 100
        });
        setBudgets(sData.budgets || MOCK_BUDGETS);
        setIsOffline(false);

        // Fetch family name
        try {
          const familyRes = await fetch(`${API_BASE}/trust/family/${familyId}`);
          if (familyRes.ok) {
            const fData = await familyRes.json();
            if (fData.name) setFamilyName(fData.name);
          }
        } catch (e) { console.error("Failed to fetch family name:", e); }

        // Fetch family members dynamically from backend
        try {
          const membersRes = await fetch(`${API_BASE}/trust/members/${familyId}`);
          if (membersRes.ok) {
            const mData = await membersRes.json();
            const langMap: Record<string, string> = {
              en: "English",
              hi: "Hindi",
              ta: "Tamil",
              ml: "Malayalam",
              te: "Telugu"
            };
            const mappedMembers = mData.map((m: any) => ({
              id: m.id,
              name: m.name,
              role: m.role,
              phone_number: m.phone_number,
              language: langMap[m.preferred_language] || m.preferred_language,
              voice: m.role !== "Son" && m.role.toLowerCase() !== "son"
            }));
            setMembers(mappedMembers);
          }
        } catch (memberErr) {
          console.error("Failed to fetch family members:", memberErr);
        }
        
        // Update goals from database
        if (sData.goals && sData.goals.length > 0) {
          const dbGoals = sData.goals.map((g: any) => ({
            id: g.id,
            name: g.goal_name,
            current: g.current_amount,
            target: g.target_amount,
            target_date: g.target_date,
            est: `Target: ${new Date(g.target_date).toLocaleDateString("en-IN", { month: "short", year: "numeric" })}`
          }));
          setGoals(dbGoals);
        }
      }

      const pendingRes = await fetch(`${API_BASE}/trust/pending-confirmations/${familyId}`);
      if (pendingRes.ok) {
        const pData = await pendingRes.json();
        setPendingLow(pData.low_confidence_requests || []);
        setPendingMed(pData.medium_confidence_expenses || []);
        
        // Populate edit state dictionary with current raw values
        const initialEdits: Record<string, any> = {};
        pData.low_confidence_requests.forEach((r: any) => {
          initialEdits[r.id] = {
            amount: r.raw_value.amount,
            category: r.raw_value.category || "misc",
            description: r.raw_value.description || "",
            lender_name: r.raw_value.lender_name || "",
            borrower_name: r.raw_value.borrower_name || "",
            due_date: r.raw_value.due_date || "",
            note: r.raw_value.note || ""
          };
        });
        setEditRequestValues(prev => ({ ...prev, ...initialEdits }));
      }

      const timelineRes = await fetch(`${API_BASE}/trust/timeline/${familyId}`);
      if (timelineRes.ok) {
        const tData = await timelineRes.json();
        setTimeline(tData || []);
      }

      const insightGenRes = await fetch(`${API_BASE}/insights/generate/${familyId}`, { method: "POST" });
      if (insightGenRes.ok) {
        const iData = await insightGenRes.json();
        setInsights(iData.insights || []);
      }

      // Compile chronological transaction ledger from confirmed expenses & active debts in SQLite
      let combined: any[] = [];
      if (summaryData.expenses) {
        const dbExpenses = (summaryData.expenses || []).map((exp: any) => ({
          id: exp.id,
          amount: exp.amount,
          category: exp.category,
          logged_by: exp.members?.name || "Ramesh",
          type: (exp.call_id && !exp.call_id.startsWith("manual")) ? "voice" : "manual",
          item_type: "expense",
          description: exp.description || `Spent on ${exp.category}`,
          timestamp: exp.created_at || exp.date,
          status: exp.status
        }));
        
        const dbDebts = (summaryData.active_debts || []).map((d: any) => ({
          id: d.id,
          amount: d.amount,
          category: "debt",
          logged_by: d.borrower_name || "Ramesh",
          lender_name: d.lender_name,
          borrower_name: d.borrower_name,
          type: (d.call_id && !d.call_id.startsWith("manual")) ? "voice" : "manual",
          item_type: "debt",
          description: d.note || `Owed to ${d.lender_name}`,
          timestamp: d.created_at || new Date().toISOString(),
          status: d.status
        }));

        combined = [...dbExpenses, ...dbDebts].sort(
          (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        );
      }
      setTransactions(combined);

    } catch (err) {
      console.log("Using Mock Memory: Local API server offline.", err);
      setIsOffline(true);
    }
  };

  useEffect(() => {
    loadData(selectedFamily);
  }, [selectedFamily]);

  // Actions
  const verifyMediumExpense = async (expenseId: string) => {
    if (isOffline) {
      setPendingMed(prev => prev.filter(e => e.id !== expenseId));
      setTransactions(prev => prev.map(tx => tx.id === expenseId ? { ...tx, status: "confirmed" } : tx));
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/trust/verify-expense/${expenseId}`, { method: "POST" });
      if (res.ok) {
        loadData(selectedFamily);
      }
    } catch (e) {
      alert("Error confirming expense");
    }
  };

  const verifyLowRequest = async (requestId: string, itemType: string) => {
    const edits = editRequestValues[requestId] || {};
    if (isOffline) {
      setPendingLow(prev => prev.filter(r => r.id !== requestId));
      const mockNew = {
        id: requestId,
        amount: edits.amount,
        category: edits.category || "misc",
        logged_by: "Sunita",
        type: "voice",
        item_type: itemType,
        description: edits.description || edits.note || "Verified voice transaction",
        timestamp: new Date().toISOString(),
        status: "confirmed"
      };
      setTransactions(prev => [mockNew, ...prev]);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/trust/verify-request/${requestId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(edits)
      });
      if (res.ok) {
        loadData(selectedFamily);
      }
    } catch (e) {
      alert("Error verifying request");
    }
  };

  const discardRequest = async (requestId: string) => {
    if (isOffline) {
      setPendingLow(prev => prev.filter(r => r.id !== requestId));
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/trust/discard-request/${requestId}`, { method: "POST" });
      if (res.ok) {
        loadData(selectedFamily);
      }
    } catch (e) {
      alert("Error discarding request");
    }
  };

  const handleEditChange = (requestId: string, field: string, val: any) => {
    setEditRequestValues(prev => ({
      ...prev,
      [requestId]: {
        ...(prev[requestId] || {}),
        [field]: val
      }
    }));
  };

  // Reset Dashboard Data
  const handleResetData = async () => {
    if (isOffline) {
      setTransactions([]);
      setPendingLow([]);
      setPendingMed([]);
      setTimeline([]);
      setStats({
        total_assets: 0,
        total_debts: 0,
        savings_rate: 0,
        health_score: 100
      });
      setBudgets(prev => prev.map(b => ({ ...b, spent: 0, remaining: b.limit })));
      setGoals(prev => prev.map(g => ({ ...g, current: 0 })));
      alert("Simulated database reset successfully.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/trust/reset-data/${selectedFamily}`, {
        method: "POST"
      });
      if (res.ok) {
        alert("Family database entries successfully cleared!");
        loadData(selectedFamily);
      } else {
        alert("Failed to reset database.");
      }
    } catch (err) {
      alert("Error: Could not connect to reset endpoint.");
    }
  };

  // Add Manual Expense Handler
  const handleAddExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (expAmount <= 0) return;

    const selectedMember = members.find(m => m.name === expSpeaker);
    const payload = {
      phone_number: selectedMember?.phone_number || "+910000000000",
      member_name: expSpeaker,
      call_id: `manual-exp-${Date.now()}`,
      amount: expAmount,
      category: expCategory,
      description: expDesc || `Manual expense log`,
      confidence: 1.0
    };

    if (isOffline) {
      const newExp = {
        id: payload.call_id,
        amount: expAmount,
        category: expCategory,
        logged_by: expSpeaker,
        type: "manual",
        item_type: "expense",
        description: expDesc || `Manual expense log`,
        timestamp: new Date().toISOString(),
        status: "confirmed"
      };
      setTransactions(prev => [newExp, ...prev]);
      
      // Update budgets spent
      setBudgets(prev => prev.map(b => {
        if (b.category === expCategory) {
          const spent = b.spent + expAmount;
          return { ...b, spent, remaining: b.limit - spent };
        }
        return b;
      }));
      setStats(prev => ({ ...prev, total_assets: prev.total_assets - expAmount }));
      
      setIsAddTransactionOpen(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/tools/record-expense`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setIsAddTransactionOpen(false);
        setExpAmount(0);
        setExpDesc("");
        loadData(selectedFamily);
      }
    } catch (err) {
      alert("Offline: Could not record manual expense.");
    }
  };

  // Add Manual Debt Handler
  const handleAddDebt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (debtAmount <= 0) return;

    const selectedMember = members.find(m => m.name === debtSpeaker);
    const payload = {
      phone_number: selectedMember?.phone_number || "+910000000000",
      member_name: debtSpeaker,
      call_id: `manual-debt-${Date.now()}`,
      lender_name: debtLender,
      borrower_name: debtBorrower,
      amount: debtAmount,
      due_date: debtDueDate,
      note: debtNote || `Owed to ${debtLender}`,
      confidence: 1.0
    };

    if (isOffline) {
      const newDebt = {
        id: payload.call_id,
        amount: debtAmount,
        category: "debt",
        logged_by: debtSpeaker,
        type: "manual",
        item_type: "debt",
        description: debtNote || `Owed to ${debtLender}`,
        timestamp: new Date().toISOString(),
        status: "active"
      };
      setTransactions(prev => [newDebt, ...prev]);
      setStats(prev => ({ ...prev, total_debts: prev.total_debts + debtAmount }));
      setIsAddTransactionOpen(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/tools/record-debt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setIsAddTransactionOpen(false);
        setDebtAmount(0);
        setDebtNote("");
        loadData(selectedFamily);
      }
    } catch (err) {
      alert("Offline: Could not record manual debt.");
    }
  };

  // Edit Family Member details
  const triggerEditMember = (m: any) => {
    setEditingMember(m);
    setMemberLang(m.language);
    setMemberRole(m.role);
    setMemberVoice(m.voice);
    setMemberPhone(m.phone_number || "");
    setIsEditMemberOpen(true);
  };

  const handleEditMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingMember) return;

    const langCodeMap: Record<string, string> = {
      English: "en",
      Hindi: "hi",
      Tamil: "ta",
      Malayalam: "ml",
      Telugu: "te"
    };

    const payload = {
      name: editingMember.name,
      role: memberRole,
      phone_number: memberPhone,
      preferred_language: langCodeMap[memberLang] || "en"
    };

    if (isOffline) {
      setMembers(prev => prev.map(m => {
        if (m.name === editingMember.name) {
          return {
            ...m,
            role: memberRole,
            language: memberLang,
            phone_number: memberPhone,
            voice: memberVoice
          };
        }
        return m;
      }));
      setIsEditMemberOpen(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/trust/members/${editingMember.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setIsEditMemberOpen(false);
        loadData(selectedFamily);
      } else {
        alert("Failed to update profile updates in backend.");
      }
    } catch (err) {
      alert("Error: Could not connect to update profile endpoint.");
    }
  };

  // ====== BUDGET CRUD HANDLERS ======
  const handleUpdateBudget = async (budgetId: string) => {
    if (editingBudgetLimit <= 0) return;
    try {
      const res = await fetch(`${API_BASE}/trust/budget/${budgetId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ monthly_limit: editingBudgetLimit })
      });
      if (res.ok) {
        setEditingBudgetId(null);
        loadData(selectedFamily);
      }
    } catch (err) { alert("Failed to update budget."); }
  };

  const handleCreateBudget = async () => {
    if (!newBudgetCategory.trim() || newBudgetLimit <= 0) return;
    try {
      const res = await fetch(`${API_BASE}/trust/budget`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ family_id: selectedFamily, category: newBudgetCategory.toLowerCase().trim(), monthly_limit: newBudgetLimit })
      });
      if (res.ok) {
        setIsAddBudgetOpen(false);
        setNewBudgetCategory("");
        setNewBudgetLimit(0);
        loadData(selectedFamily);
      }
    } catch (err) { alert("Failed to create budget."); }
  };

  const handleDeleteBudget = async (budgetId: string) => {
    if (!confirm("Delete this budget category?")) return;
    try {
      const res = await fetch(`${API_BASE}/trust/budget/${budgetId}`, { method: "DELETE" });
      if (res.ok) loadData(selectedFamily);
    } catch (err) { alert("Failed to delete budget."); }
  };

  // ====== GOAL CRUD HANDLERS ======
  const handleUpdateGoal = async (goalId: string) => {
    if (!editingGoalData.goal_name.trim() || editingGoalData.target_amount <= 0) return;
    try {
      const res = await fetch(`${API_BASE}/trust/goal/${goalId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editingGoalData)
      });
      if (res.ok) {
        setEditingGoalId(null);
        loadData(selectedFamily);
      }
    } catch (err) { alert("Failed to update goal."); }
  };

  const handleCreateGoal = async () => {
    if (!newGoalName.trim() || newGoalTarget <= 0 || !newGoalDate) return;
    try {
      const res = await fetch(`${API_BASE}/trust/goal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ family_id: selectedFamily, goal_name: newGoalName.trim(), target_amount: newGoalTarget, target_date: newGoalDate, importance_level: "high" })
      });
      if (res.ok) {
        setIsAddGoalOpen(false);
        setNewGoalName("");
        setNewGoalTarget(0);
        setNewGoalDate("");
        loadData(selectedFamily);
      }
    } catch (err) { alert("Failed to create goal."); }
  };

  const handleDeleteGoal = async (goalId: string) => {
    if (!confirm("Delete this savings goal?")) return;
    try {
      const res = await fetch(`${API_BASE}/trust/goal/${goalId}`, { method: "DELETE" });
      if (res.ok) loadData(selectedFamily);
    } catch (err) { alert("Failed to delete goal."); }
  };

  // ====== FAMILY NAME HANDLER ======
  const handleUpdateFamilyName = async () => {
    if (!editFamilyNameValue.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/trust/family/${selectedFamily}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: editFamilyNameValue.trim() })
      });
      if (res.ok) {
        setFamilyName(editFamilyNameValue.trim());
        setIsEditingFamilyName(false);
      }
    } catch (err) { alert("Failed to update family name."); }
  };

  // Delete transaction handler
  const handleDeleteTransaction = async (tx: any) => {
    if (!window.confirm("Are you sure you want to delete this transaction from family memory?")) return;
    
    if (isOffline) {
      setTransactions(prev => prev.filter(t => t.id !== tx.id));
      return;
    }
    
    try {
      const endpoint = tx.item_type === "expense" 
        ? `${API_BASE}/trust/expense/${tx.id}`
        : `${API_BASE}/trust/debt/${tx.id}`;
      const res = await fetch(endpoint, { method: "DELETE" });
      if (res.ok) {
        loadData(selectedFamily);
      } else {
        alert("Failed to delete transaction");
      }
    } catch (e) {
      alert("Error deleting transaction");
    }
  };

  // Start edit transaction handler
  const handleStartEdit = (tx: any) => {
    setEditingTransaction(tx);
    setEditTxAmount(tx.amount);
    setEditTxCategory(tx.category);
    setEditTxDesc(tx.description);
    if (tx.item_type === "debt") {
      setEditTxLender(tx.lender_name || "Uncle Vinay");
      setEditTxBorrower(tx.borrower_name || "Ramesh");
    }
  };

  // Save edit transaction handler
  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTransaction) return;

    if (isOffline) {
      setTransactions(prev => prev.map(t => {
        if (t.id === editingTransaction.id) {
          return {
            ...t,
            amount: editTxAmount,
            category: editTxCategory,
            description: editTxDesc
          };
        }
        return t;
      }));
      setEditingTransaction(null);
      return;
    }

    try {
      const endpoint = editingTransaction.item_type === "expense" 
        ? `${API_BASE}/trust/expense/${editingTransaction.id}`
        : `${API_BASE}/trust/debt/${editingTransaction.id}`;
      
      const payload = editingTransaction.item_type === "expense" 
        ? { amount: editTxAmount, category: editTxCategory, description: editTxDesc }
        : { amount: editTxAmount, lender_name: editTxLender, borrower_name: editTxBorrower, note: editTxDesc };

      const res = await fetch(endpoint, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setEditingTransaction(null);
        loadData(selectedFamily);
      } else {
        alert("Failed to update transaction");
      }
    } catch (e) {
      alert("Error saving transaction updates");
    }
  };


  // Text-only assistant query parser using family memory and stats
  const submitSimulatorQuery = async (queryText: string) => {
    if (!queryText.trim()) return;

    const userMessage = queryText;
    setSimLogs(prev => [...prev, { sender: "user", text: userMessage }]);
    setSimLoading(true);
    setAgentState("Thinking");

    setTimeout(async () => {
      try {
        const lowercaseText = userMessage.toLowerCase();
        
        // 1. Greetings
        const isGreeting = /^(hi|hello|hey|greetings|good morning|good evening|yo|namaste)/.test(lowercaseText) || 
                           lowercaseText.trim() === "hi" || 
                           lowercaseText.trim() === "hello";
        if (isGreeting) {
          setSimLogs(prev => [...prev, {
            sender: "assistant",
            text: `Hello, ${simSpeaker}! I am your Family Financial Assistant. How can I help you today? You can ask me about budgets, debts, savings goals, or general financial literacy concepts.`
          }]);
          setAgentState("Idle");
          setSimLoading(false);
          return;
        }

        // 2. Spending Query
        if (lowercaseText.includes("spend") || lowercaseText.includes("spent") || lowercaseText.includes("how much did we spend")) {
          const totalLimit = budgets.reduce((acc, b) => acc + b.limit, 0);
          const totalSpent = budgets.reduce((acc, b) => acc + b.spent, 0);
          const remaining = totalLimit - totalSpent;
          
          setSimLogs(prev => [...prev, {
            sender: "assistant",
            text: `This month, the family has spent ₹${totalSpent.toLocaleString("en-IN")} out of a total category limit of ₹${totalLimit.toLocaleString("en-IN")}. You have ₹${remaining.toLocaleString("en-IN")} available budget remaining across groceries, utilities, fuel, and tuition.`
          }]);
          setAgentState("Idle");
          setSimLoading(false);
          return;
        }

        // 3. Overspending check
        if (lowercaseText.includes("overspend") || lowercaseText.includes("over budget") || lowercaseText.includes("overspending")) {
          const over = budgets.filter(b => b.spent > b.limit);
          const critical = budgets.filter(b => b.spent >= b.limit * 0.8 && b.spent <= b.limit);
          let responseText = "";
          if (over.length > 0) {
            responseText += `Alert: We have exceeded the monthly budget limit in: ${over.map(b => `${b.category} (by ₹${(b.spent - b.limit).toLocaleString("en-IN")})`).join(", ")}. `;
          }
          if (critical.length > 0) {
            responseText += `Warning: We are close to the limit (80%+) in: ${critical.map(b => `${b.category} (₹${b.remaining.toLocaleString("en-IN")} left)`).join(", ")}. `;
          }
          if (over.length === 0 && critical.length === 0) {
            responseText = "Great news! All budgets are currently on track and within limits this month.";
          }
          setSimLogs(prev => [...prev, { sender: "assistant", text: responseText }]);
          setAgentState("Idle");
          setSimLoading(false);
          return;
        }

        // 4. Affordability check
        if (lowercaseText.includes("afford") || lowercaseText.includes("can we buy") || lowercaseText.includes("can we purchase")) {
          const match = lowercaseText.match(/\d+/);
          const purchaseAmount = match ? parseInt(match[0], 10) : 0;
          
          const totalLimit = budgets.reduce((acc, b) => acc + b.limit, 0);
          const totalSpent = budgets.reduce((acc, b) => acc + b.spent, 0);
          const remaining = totalLimit - totalSpent;

          if (purchaseAmount === 0) {
            setSimLogs(prev => [...prev, {
              sender: "assistant",
              text: "Could you specify the amount of the purchase? For example, ask 'Can we afford a purchase of 5000 rupees?'"
            }]);
          } else if (purchaseAmount <= remaining) {
            setSimLogs(prev => [...prev, {
              sender: "assistant",
              text: `Yes, we can afford this purchase of ₹${purchaseAmount.toLocaleString("en-IN")}. It fits within your remaining monthly budget of ₹${remaining.toLocaleString("en-IN")}, leaving you with ₹${(remaining - purchaseAmount).toLocaleString("en-IN")} for other expenses.`
            }]);
          } else {
            setSimLogs(prev => [...prev, {
              sender: "assistant",
              text: `No, a purchase of ₹${purchaseAmount.toLocaleString("en-IN")} exceeds your remaining monthly budget of ₹${remaining.toLocaleString("en-IN")} by ₹${(purchaseAmount - remaining).toLocaleString("en-IN")}. I recommend postponing this purchase or allocating from your savings goal.`
            }]);
          }
          setAgentState("Idle");
          setSimLoading(false);
          return;
        }

        // 5. Debt Reduction
        if (lowercaseText.includes("reduce debt") || lowercaseText.includes("debt reduction") || lowercaseText.includes("pay off debt") || lowercaseText.includes("repay debt")) {
          setSimLogs(prev => [...prev, {
            sender: "assistant",
            text: `You currently have ₹${stats.total_debts.toLocaleString("en-IN")} in active debts. I recommend the Debt Avalanche method: prioritize paying off high-interest or short-term obligations first. Currently, Uncle Vinay (₹8,000) has the nearest due date (in 5 days) and should be paid off first to avoid delinquency.`
          }]);
          setAgentState("Idle");
          setSimLoading(false);
          return;
        }

        // 6. Savings Goals saving advice
        if (lowercaseText.includes("goal") || lowercaseText.includes("save") || lowercaseText.includes("savings")) {
          const totalTarget = goals.reduce((acc, g) => acc + g.target, 0);
          const totalCurrent = goals.reduce((acc, g) => acc + g.current, 0);
          const percent = totalTarget > 0 ? (totalCurrent / totalTarget) * 100 : 0;
          
          setSimLogs(prev => [...prev, {
            sender: "assistant",
            text: `The family has saved ₹${totalCurrent.toLocaleString("en-IN")} out of a total goals target of ₹${totalTarget.toLocaleString("en-IN")} (${percent.toFixed(0)}%). For your Vacation Savings goal (target Dec 2026), you need to save ₹${Math.round((80000 - goals[2].current) / 6).toLocaleString("en-IN")} monthly.`
          }]);
          setAgentState("Idle");
          setSimLoading(false);
          return;
        }

        // 7. Literacy concept checks
        const isLiteracy = lowercaseText.includes("explain") || lowercaseText.includes("what is") || lowercaseText.includes("ppf") || lowercaseText.includes("compound") || lowercaseText.includes("sukanya") || lowercaseText.includes("fd") || lowercaseText.includes("fixed deposit") || lowercaseText.includes("emergency");
        if (isLiteracy) {
          const res = await fetch(`${API_BASE}/tools/get-financial-literacy`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: userMessage })
          });
          if (res.ok) {
            const data = await res.json();
            setSimLogs(prev => [...prev, { sender: "assistant", text: data.voice_response }]);
          } else {
            setSimLogs(prev => [...prev, { sender: "assistant", text: "I can explain safe household savings like Fixed Deposits, Public Provident Fund (PPF), or compounding." }]);
          }
          setAgentState("Idle");
          setSimLoading(false);
          return;
        }

        // Fallback or generic help
        setSimLogs(prev => [...prev, {
          sender: "assistant",
          text: `I understood your question: "${userMessage}". However, I need to consult the family memory. I can explain savings schemes (PPF, FD), check remaining budgets, debt repayment, or log expenses if you state the amount, e.g. "I spent 500 on groceries".`
        }]);
        setAgentState("Idle");
        setSimLoading(false);

      } catch (err) {
        setSimLogs(prev => [...prev, { sender: "assistant", text: "Offline: I couldn't reach the FastAPI server, but I can assist with local memory questions." }]);
        setAgentState("Idle");
        setSimLoading(false);
      }
    }, 800);
  };

  const runSimulatorText = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!simText.trim()) return;
    submitSimulatorQuery(simText);
    setSimText("");
  };

  const runTemplateSpeak = (text: string) => {
    setSimText(text);
  };

  // Helper formatting for timeline intents and metadata
  const getTimelineIntent = (call: any) => {
    if (call.intent) return call.intent;
    if (call.extracted_json?.expense) return "Expense Logging";
    if (call.extracted_json?.debt) return "Debt Logging";
    if (call.extracted_json?.budget) return "Budget Check";
    return "Voice Query";
  };

  const getTimelineTool = (call: any) => {
    if (call.extracted_json?.expense) return "record-expense";
    if (call.extracted_json?.debt) return "record-debt";
    if (call.extracted_json?.budget) return "budget-status";
    return "get-literacy";
  };

  const getTimelineLang = (call: any) => {
    return call.language || "English";
  };

  const getStructuredInsight = (ins: any) => {
    if (ins.insight_type === "overspending" || ins.title?.toLowerCase().includes("fuel")) {
      return {
        type: "Budget Insight",
        title: ins.title,
        explanation: "You spent 15% more on groceries/fuel this month compared to seasonal forecasts.",
        why: "Vehicle fuel rates are higher; grocery spending spiked last week.",
        action: "Review limits or pool resources this weekend.",
        typeClass: "overspending"
      };
    }
    if (ins.insight_type === "savings_nudge" || ins.title?.toLowerCase().includes("ppf")) {
      return {
        type: "Wealth Building Tip",
        title: "PPF Advantage",
        explanation: "Government-backed and tax-efficient compound savings program.",
        why: "A surplus exists in your utilities budget (₹2,800 currently unspent).",
        action: "Consider transferring ₹1,000 monthly to earn compound tax-free yields.",
        typeClass: "savings_nudge"
      };
    }
    return {
      type: ins.insight_type === "savings_nudge" ? "Savings Nudge" : "Debt Reduction Suggestion",
      title: ins.title,
      explanation: ins.description,
      why: `Evaluated dynamically from ${familyName} money ledger.`,
      action: "Review suggested repayment strategies.",
      typeClass: ins.insight_type
    };
  };

  const formatTimestamp = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      const now = new Date();
      
      const isToday = date.getDate() === now.getDate() && 
                      date.getMonth() === now.getMonth() && 
                      date.getFullYear() === now.getFullYear();
                      
      const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      
      if (isToday || dateStr.includes("Just now")) {
        return `Today • ${timeStr}`;
      }
      
      const yesterday = new Date();
      yesterday.setDate(now.getDate() - 1);
      const isYesterday = date.getDate() === yesterday.getDate() && 
                          date.getMonth() === yesterday.getMonth() && 
                          date.getFullYear() === yesterday.getFullYear();
      if (isYesterday) {
        return `Yesterday • ${timeStr}`;
      }
      
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' }) + " • " + timeStr;
    } catch {
      return "Just now";
    }
  };

  // Render Overview Tab Content
  const renderOverview = () => {
    const totalLimit = budgets.reduce((acc, b) => acc + b.limit, 0);
    const totalSpent = budgets.reduce((acc, b) => acc + b.spent, 0);
    const availableBudget = totalLimit - totalSpent;
    const totalGoalSaved = goals.reduce((acc, g) => acc + g.current, 0);

    // Calculate dynamic monthly spending from confirmed expenses
    const currentMonthExpenses = transactions.filter(tx => {
      if (tx.item_type !== "expense") return false;
      const date = new Date(tx.timestamp);
      const now = new Date();
      return date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear();
    });
    const monthlySpending = currentMonthExpenses.reduce((sum, tx) => sum + tx.amount, 0);

    // Dynamic health status
    let healthStatus = "Excellent";
    let healthColor = "green";
    if (stats.health_score < 70) {
      healthStatus = "Needs Attention";
      healthColor = "red";
    } else if (stats.health_score < 90) {
      healthStatus = "Good";
      healthColor = "gold";
    }

    // Filtered Activity Feed Transactions
    const feedTransactions = transactions.filter(tx => {
      const matchMember = feedFilterMember === "All" || tx.logged_by.toLowerCase() === feedFilterMember.toLowerCase();
      const matchType = feedFilterType === "All" || 
                        (feedFilterType === "Voice" && tx.type === "voice") || 
                        (feedFilterType === "Manual" && tx.type === "manual");
      return matchMember && matchType;
    });

    return (
      <div className="tab-pane-content animate-fade-in">
        {/* Top Header Greetings */}
        <div className="greeting-section">
          <div className="greeting-text">
            <h2>Good Evening, {familyName}</h2>
            <p>Here is your financial status overview</p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", position: "relative" }}>
            <div className="info-tooltip-container" style={{ position: "relative", cursor: "help", display: "flex", alignItems: "center" }}>
              <Info size={20} color="hsl(var(--text-muted))" />
              <div className="info-tooltip" style={{
                position: "absolute",
                top: "100%",
                right: "0",
                marginTop: "10px",
                width: "320px",
                backgroundColor: "#fff",
                border: "1px solid hsl(var(--border))",
                borderRadius: "12px",
                padding: "16px",
                boxShadow: "0 10px 25px rgba(0,0,0,0.1)",
                zIndex: 100,
                display: "none",
                flexDirection: "column",
                gap: "8px"
              }}>
                <h4 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: "hsl(var(--text-primary))" }}>How to use this platform:</h4>
                <ol style={{ margin: 0, paddingLeft: "20px", fontSize: "0.85rem", color: "hsl(var(--text-secondary))", lineHeight: 1.5, display: "flex", flexDirection: "column", gap: "6px" }}>
                  <li><strong>Call Bolna:</strong> Dial the inbound number to reach your AI assistant.</li>
                  <li><strong>Identify:</strong> Tell the AI your name (e.g. "I am Guest").</li>
                  <li><strong>Log:</strong> Say what you spent or borrowed (e.g. "I spent 500 on fuel").</li>
                  <li><strong>Review:</strong> View your live transactions appearing on this dashboard instantly.</li>
                </ol>
              </div>
              <style dangerouslySetInnerHTML={{__html: `
                .info-tooltip-container:hover .info-tooltip { display: flex !important; }
                .info-tooltip-container:hover svg { color: hsl(var(--accent-green)) !important; }
              `}} />
            </div>
            <select 
              className="family-dropdown"
              style={{ fontSize: "0.85rem", padding: "6px 12px", margin: 0 }}
              value={selectedFamily}
              onChange={(e) => setSelectedFamily(e.target.value)}
            >
              <option value={MOCK_FAMILY_ID}>{familyName} ▼</option>
            </select>
          </div>
        </div>

        {/* Dynamic Financial Health Score */}
        <div className="premium-card" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "20px" }}>
          <div>
            <h3 style={{ fontSize: "1.05rem", fontWeight: 700, margin: 0 }}>Family Financial Health</h3>
            <p style={{ fontSize: "0.85rem", color: "hsl(var(--text-secondary))", margin: "4px 0 0 0" }}>
              Your household savings and debt indices are looking strong.
            </p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{ textAlign: "right" }}>
              <span style={{ fontSize: "1.6rem", fontWeight: 800 }}>{stats.health_score}</span>
              <span style={{ fontSize: "0.85rem", color: "hsl(var(--text-muted))" }}>/100</span>
              <span className={`review-badge`} style={{ display: "block", marginTop: "2px", backgroundColor: `hsla(var(--accent-${healthColor}), 0.1)`, color: `hsl(var(--accent-${healthColor}))` }}>
                {healthStatus}
              </span>
            </div>
          </div>
        </div>

        {/* Trust Layer review banners inline */}
        {(pendingLow.length > 0 || pendingMed.length > 0) && (
          <div className="premium-card" style={{ borderLeft: "4px solid hsl(var(--accent-gold))", backgroundColor: "hsla(var(--accent-gold), 0.02)" }}>
            <div className="review-card-top">
              <span className="review-badge" style={{ backgroundColor: "hsla(var(--accent-gold), 0.15)", color: "hsl(var(--accent-gold))" }}>Review Pending Updates</span>
              <span style={{ fontSize: "0.75rem", color: "hsl(var(--text-muted))", fontWeight: 600 }}>Trust Layer</span>
            </div>
            <p className="review-text" style={{ margin: "8px 0 16px 0", fontSize: "0.9rem" }}>
              We found <strong>{pendingLow.length + pendingMed.length}</strong> recent voice updates that require confirmation before committing to family memory.
            </p>
            
            {/* List of pending items to confirm/edit/reject inline */}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {pendingMed.map((exp) => (
                <div key={exp.id} style={{ padding: "12px", borderRadius: "12px", border: "1px dashed hsla(var(--accent-gold), 0.4)", backgroundColor: "#ffffff" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "hsl(var(--text-muted))", marginBottom: "6px" }}>
                    <span>Source: Phone Call ({exp.members?.name || "Ramesh"})</span>
                    <span style={{ fontWeight: 600, color: "hsl(var(--accent-gold))" }}>Needs Review</span>
                  </div>
                  <p style={{ fontSize: "0.85rem", margin: "0 0 8px 0" }}>
                    Logged <strong>₹{exp.amount}</strong> for <strong>{exp.category}</strong>: &ldquo;{exp.description}&rdquo;
                  </p>
                  <div className="review-actions">
                    <button onClick={() => discardRequest(exp.id)} className="btn-review discard" style={{ padding: "4px 10px", fontSize: "0.75rem" }}>Discard</button>
                    <button onClick={() => verifyMediumExpense(exp.id)} className="btn-review confirm" style={{ padding: "4px 10px", fontSize: "0.75rem" }}>Confirm</button>
                  </div>
                </div>
              ))}

              {pendingLow.map((req) => {
                const edits = editRequestValues[req.id] || {};
                const isExpense = req.item_type === "expense";
                return (
                  <div key={req.id} style={{ padding: "12px", borderRadius: "12px", border: "1px dashed hsla(var(--accent-red), 0.4)", backgroundColor: "#ffffff" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "hsl(var(--text-muted))", marginBottom: "6px" }}>
                      <span>Source: Voice Entry</span>
                      <span style={{ fontWeight: 600, color: "hsl(var(--accent-red))" }}>Pending Verification</span>
                    </div>
                    <p style={{ fontSize: "0.8rem", fontStyle: "italic", margin: "0 0 8px 0" }}>
                      Heard: &ldquo;{isExpense ? req.raw_value.description : req.raw_value.note}&rdquo;
                    </p>
                    
                    <div className="trust-card-inputs" style={{ display: "flex", gap: "8px", marginBottom: "8px" }}>
                      <div style={{ flex: 1 }}>
                        <label style={{ fontSize: "0.65rem", fontWeight: 700, color: "hsl(var(--text-secondary))" }}>Amount</label>
                        <input 
                          type="number" 
                          className="form-input"
                          style={{ padding: "4px 8px", fontSize: "0.8rem" }}
                          value={edits.amount || ""}
                          onChange={(e) => handleEditChange(req.id, "amount", parseFloat(e.target.value) || 0)}
                        />
                      </div>
                      <div style={{ flex: 1 }}>
                        <label style={{ fontSize: "0.65rem", fontWeight: 700, color: "hsl(var(--text-secondary))" }}>
                          {isExpense ? "Category" : "Lender"}
                        </label>
                        {isExpense ? (
                          <select 
                            className="form-input"
                            style={{ padding: "4px 8px", fontSize: "0.8rem", height: "30px" }}
                            value={edits.category || "misc"}
                            onChange={(e) => handleEditChange(req.id, "category", e.target.value)}
                          >
                            <option value="groceries">Groceries</option>
                            <option value="utilities">Utilities</option>
                            <option value="fuel">Fuel</option>
                            <option value="tuition">Tuition</option>
                            <option value="misc">Misc</option>
                          </select>
                        ) : (
                          <input 
                            type="text" 
                            className="form-input"
                            style={{ padding: "4px 8px", fontSize: "0.8rem" }}
                            value={edits.lender_name || ""}
                            onChange={(e) => handleEditChange(req.id, "lender_name", e.target.value)}
                          />
                        )}
                      </div>
                    </div>

                    <div className="review-actions">
                      <button onClick={() => discardRequest(req.id)} className="btn-review discard" style={{ padding: "4px 10px", fontSize: "0.75rem" }}>Discard</button>
                      <button onClick={() => verifyLowRequest(req.id, req.item_type)} className="btn-review confirm" style={{ padding: "4px 10px", fontSize: "0.75rem" }}>Confirm</button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Snapshot Cards */}
        <div className="premium-card">
          <h3 className="sub-title" style={{ margin: "0 0 16px 0", fontSize: "1rem" }}>Monthly Financial Snapshot</h3>
          <div className="snapshot-grid">
            <div className="snapshot-item">
              <span className="snapshot-label">Total Assets</span>
              <span className="snapshot-value">₹{stats.total_assets.toLocaleString("en-IN")}</span>
            </div>
            <div className="snapshot-item">
              <span className="snapshot-label">Monthly Spending</span>
              <span className="snapshot-value text-red">₹{monthlySpending.toLocaleString("en-IN")}</span>
            </div>
            <div className="snapshot-item">
              <span className="snapshot-label">Available Budget</span>
              <span className="snapshot-value green">₹{availableBudget.toLocaleString("en-IN")}</span>
            </div>
            <div className="snapshot-item">
              <span className="snapshot-label">Active Debt</span>
              <span className="snapshot-value red">₹{stats.total_debts.toLocaleString("en-IN")}</span>
            </div>
          </div>
        </div>

        {/* Unified Family Activity Feed */}
        <div className="premium-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", marginBottom: "16px" }}>
            <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700 }}>Family Activity Feed</h3>
            
            {/* Feed Filters */}
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <select 
                className="family-dropdown" 
                style={{ fontSize: "0.75rem", padding: "4px 8px" }} 
                value={feedFilterMember} 
                onChange={(e) => setFeedFilterMember(e.target.value)}
              >
                <option value="All">All Members</option>
                {members.map(m => (
                  <option key={m.name} value={m.name}>{m.name}</option>
                ))}
              </select>

              <select 
                className="family-dropdown" 
                style={{ fontSize: "0.75rem", padding: "4px 8px" }} 
                value={feedFilterType} 
                onChange={(e) => setFeedFilterType(e.target.value)}
              >
                <option value="All">All Channels</option>
                <option value="Voice">Voice Calls</option>
                <option value="Manual">Manual Entries</option>
              </select>
            </div>
          </div>

          <div className="activity-feed-list">
            {feedTransactions.length === 0 ? (
              <div style={{ textAlign: "center", padding: "24px", color: "hsl(var(--text-muted))" }}>
                No recent activity matches these filters.
              </div>
            ) : (
              feedTransactions.slice(0, 8).map((tx, idx) => {
                const isVoice = tx.type === "voice";
                const isExpanded = expandedActivityId === tx.id;
                // Simplified status categories
                const statusCategory = tx.status === "confirmed" ? "Confirmed" : tx.status === "active" ? "Confirmed" : "Needs Review";

                return (
                  <div key={tx.id || idx} style={{ borderBottom: "1px solid hsl(var(--border-dim))", padding: "12px 0" }}>
                    <div 
                      style={{ display: "flex", alignItems: "flex-start", gap: "12px", cursor: "pointer" }} 
                      onClick={() => setExpandedActivityId(isExpanded ? null : tx.id)}
                    >
                      <div className="activity-circle" style={{ backgroundColor: isVoice ? "hsla(var(--accent-green), 0.08)" : "hsla(var(--accent-blue), 0.08)", color: isVoice ? "hsl(var(--accent-green))" : "hsl(var(--accent-blue))" }}>
                        {tx.logged_by ? tx.logged_by[0] : "F"}
                      </div>
                      <div style={{ flex: 1 }}>
                        <p style={{ margin: 0, fontSize: "0.88rem", fontWeight: 600 }}>
                          {tx.logged_by} logged an {tx.item_type} of <strong>₹{tx.amount.toLocaleString("en-IN")}</strong>
                        </p>
                        <p style={{ margin: "3px 0 0 0", fontSize: "0.8rem", color: "hsl(var(--text-secondary))" }}>
                          &ldquo;{tx.description}&rdquo;
                        </p>
                        <div style={{ display: "flex", gap: "8px", marginTop: "6px", alignItems: "center" }}>
                          <span className={`log-type-chip ${tx.type}`} style={{ fontSize: "0.68rem" }}>
                            {isVoice ? "Voice Call" : "Dashboard Manual"}
                          </span>
                          <span style={{ fontSize: "0.72rem", color: "hsl(var(--text-muted))" }}>• {formatTimestamp(tx.timestamp)}</span>
                          <span style={{ fontSize: "0.72rem", color: "hsl(var(--accent-blue))", fontWeight: 600, marginLeft: "auto", display: "inline-flex", alignItems: "center", gap: "4px" }}>
                            {isExpanded ? "Show Less" : "Details"}
                          </span>
                        </div>
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="activity-details-expanded" style={{ marginTop: "10px", padding: "12px", borderRadius: "10px", backgroundColor: "hsl(var(--bg-card-subtle))", fontSize: "0.78rem", display: "flex", flexDirection: "column", gap: "6px", marginLeft: "48px" }}>
                        <div><strong>Verification Status:</strong> <span className={`review-badge`} style={{ display: "inline-block", backgroundColor: tx.status === "confirmed" || tx.status === "active" ? "hsla(var(--accent-green), 0.1)" : "hsla(var(--accent-gold), 0.1)", color: tx.status === "confirmed" || tx.status === "active" ? "hsl(var(--accent-green))" : "hsl(var(--accent-gold))", padding: "2px 6px", borderRadius: "4px", fontSize: "0.68rem" }}>{statusCategory}</span></div>
                        <div><strong>Category Allocation:</strong> <span style={{ textTransform: "capitalize" }}>{tx.category}</span></div>
                        {tx.item_type === "debt" && (
                          <>
                            <div><strong>Lender:</strong> {tx.lender_name}</div>
                            <div><strong>Borrower:</strong> {tx.borrower_name}</div>
                          </>
                        )}
                        <div><strong>Transaction ID:</strong> <code style={{ fontSize: "0.7rem", color: "hsl(var(--text-secondary))" }}>{tx.id}</code></div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    );
  };

  // Render Ledger Content
  const renderLedger = () => {
    const filtered = transactions.filter(tx => {
      const matchSearch = tx.description.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          tx.category.toLowerCase().includes(searchQuery.toLowerCase());
      const matchMember = filterMember === "All" || tx.logged_by.toLowerCase() === filterMember.toLowerCase();
      const matchCategory = filterCategory === "All" || tx.category.toLowerCase() === filterCategory.toLowerCase();
      const matchType = filterType === "All" || 
                        (filterType === "Voice" && tx.type === "voice") || 
                        (filterType === "Manual" && tx.type === "manual");
      return matchSearch && matchMember && matchCategory && matchType;
    });

    const sorted = [...filtered].sort((a, b) => {
      if (sortBy === "date-desc") {
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      } else if (sortBy === "date-asc") {
        return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
      } else if (sortBy === "amount-desc") {
        return b.amount - a.amount;
      } else if (sortBy === "amount-asc") {
        return a.amount - b.amount;
      }
      return 0;
    });

    const categories = Array.from(new Set(sorted.map(t => t.category || "misc")));

    const renderTransactionCard = (tx: any) => {
      const Icon = CATEGORY_ICONS[tx.category] || Folder;
      return (
        <div key={tx.id} className="transaction-card" style={{ padding: "14px 18px", marginBottom: "8px" }}>
          <div className="transaction-info-left">
            <div className="category-icon-box" style={{ borderRadius: "10px", width: "36px", height: "36px" }}>
              <Icon size={16} />
            </div>
            <div className="transaction-details">
              <span className="transaction-title-desc" style={{ textTransform: "none" }}>{tx.description}</span>
              <div className="transaction-meta-row" style={{ fontSize: "0.74rem" }}>
                <span style={{ fontWeight: 600 }}>{tx.logged_by}</span>
                <span className="meta-divider"></span>
                <span style={{ textTransform: "capitalize" }}>{tx.category}</span>
                <span className="meta-divider"></span>
                <span className={`log-type-chip ${tx.type}`}>
                  {tx.type === "voice" ? "Voice" : "Manual"}
                </span>
                <span className="meta-divider"></span>
                <span>{new Date(tx.timestamp).toLocaleDateString([], { month: "short", day: "numeric" })}</span>
              </div>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div className="transaction-amount-right" style={{ fontSize: "1.05rem" }}>
              ₹{tx.amount.toLocaleString("en-IN")}
            </div>
            <div style={{ display: "flex", gap: "4px" }}>
              <button onClick={() => handleStartEdit(tx)} className="btn-review edit" style={{ padding: "5px", borderRadius: "6px" }}>
                <Edit2 size={12} />
              </button>
              <button onClick={() => handleDeleteTransaction(tx)} className="btn-review discard" style={{ padding: "5px", borderRadius: "6px" }}>
                <Trash2 size={12} />
              </button>
            </div>
          </div>
        </div>
      );
    };

    return (
      <div className="animate-fade-in">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <h2 style={{ fontSize: "1.35rem", fontWeight: 800, margin: 0 }}>Family Transaction Ledger</h2>
          <div style={{ display: "flex", gap: "8px" }}>
            <button onClick={() => { setAddTxType("expense"); setIsAddTransactionOpen(true); }} className="btn-review confirm" style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.8rem", padding: "8px 14px", borderRadius: "8px" }}>
              <Plus size={14} /> Add Expense
            </button>
            <button onClick={() => { setAddTxType("debt"); setIsAddTransactionOpen(true); }} className="btn-review edit" style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.8rem", padding: "8px 14px", borderRadius: "8px" }}>
              <TrendingDown size={14} /> Record Debt
            </button>
          </div>
        </div>

        {/* Search & Filters */}
        <div className="premium-card" style={{ padding: "16px", marginBottom: "20px" }}>
          <div className="search-container" style={{ margin: 0 }}>
            <Search size={16} color="hsl(var(--text-muted))" />
            <input 
              type="text" 
              className="search-input"
              placeholder="Search descriptions, categories, members..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div style={{ display: "flex", gap: "8px", marginTop: "12px", flexWrap: "wrap", alignItems: "center" }}>
            <select className="family-dropdown" style={{ fontSize: "0.78rem", padding: "6px 12px" }} value={filterMember} onChange={(e) => setFilterMember(e.target.value)}>
              <option value="All">All Members</option>
              {members.map(m => (
                <option key={m.name} value={m.name}>{m.name}</option>
              ))}
            </select>

            <select className="family-dropdown" style={{ fontSize: "0.78rem", padding: "6px 12px" }} value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
              <option value="All">All Categories</option>
              <option value="groceries">Groceries</option>
              <option value="utilities">Utilities</option>
              <option value="fuel">Fuel</option>
              <option value="tuition">Tuition</option>
              <option value="debt">Debt Center</option>
              <option value="misc">Miscellaneous</option>
            </select>

            <select className="family-dropdown" style={{ fontSize: "0.78rem", padding: "6px 12px" }} value={filterType} onChange={(e) => setFilterType(e.target.value)}>
              <option value="All">All Channels</option>
              <option value="Voice">Voice Calls</option>
              <option value="Manual">Manual Entry</option>
            </select>

            <span style={{ borderLeft: "1px solid hsl(var(--border-dim))", height: "20px", margin: "0 4px" }}></span>

            <select className="family-dropdown" style={{ fontSize: "0.78rem", padding: "6px 12px" }} value={sortBy} onChange={(e) => setSortBy(e.target.value as any)}>
              <option value="date-desc">Newest First</option>
              <option value="date-asc">Oldest First</option>
              <option value="amount-desc">Highest Amount</option>
              <option value="amount-asc">Lowest Amount</option>
            </select>

            <button 
              onClick={() => setGroupByCategory(!groupByCategory)} 
              className={`filter-badge ${groupByCategory ? 'active' : ''}`}
              style={{ fontSize: "0.78rem", padding: "6px 12px", border: "1px solid hsl(var(--border-dim))", borderRadius: "10px" }}
            >
              {groupByCategory ? "Ungroup Categories" : "Group by Category"}
            </button>
          </div>
        </div>

        {/* Ledger items list */}
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {sorted.length === 0 ? (
            <div className="premium-card" style={{ textAlign: "center", padding: "40px" }}>
              <List size={28} style={{ color: "hsl(var(--text-muted))", marginBottom: "8px" }} />
              <p style={{ margin: 0, fontWeight: 700 }}>No matching transactions</p>
              <p style={{ margin: "4px 0 0 0", fontSize: "0.82rem", color: "hsl(var(--text-muted))" }}>Try clearing search criteria or add a manual entry.</p>
            </div>
          ) : groupByCategory ? (
            categories.map(cat => {
              const catTx = sorted.filter(t => t.category === cat);
              if (catTx.length === 0) return null;
              return (
                <div key={cat} style={{ marginBottom: "16px" }}>
                  <h3 style={{ fontSize: "0.82rem", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.05em", color: "hsl(var(--text-muted))", marginBottom: "10px", paddingLeft: "4px" }}>
                    {cat} ({catTx.length})
                  </h3>
                  {catTx.map(tx => renderTransactionCard(tx))}
                </div>
              );
            })
          ) : (
            sorted.map((tx) => renderTransactionCard(tx))
          )}
        </div>
      </div>
    );
  };

  // Render Budgets & Goals Content
  const renderBudgetsAndGoals = () => {
    const totalLimit = budgets.reduce((acc, b) => acc + b.limit, 0);
    const totalSpent = budgets.reduce((acc, b) => acc + b.spent, 0);
    const availableBudget = totalLimit - totalSpent;

    return (
      <div className="animate-fade-in">
        <h2 style={{ fontSize: "1.35rem", fontWeight: 800, marginBottom: "20px" }}>Budgets & Savings Goals</h2>

        {/* Budgets Progress */}
        <div className="premium-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 700 }}>Monthly Household Budgets</h3>
            <span style={{ fontSize: "0.8rem", color: "hsl(var(--text-secondary))" }}>
              Total: ₹{totalSpent.toLocaleString("en-IN")} spent / ₹{totalLimit.toLocaleString("en-IN")} limit
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {budgets.map((b: any, idx: number) => {
              const percent = b.limit > 0 ? Math.min((b.spent / b.limit) * 100, 100) : 0;
              let statusLabel = "On Track";
              let statusColor = "green";
              if (b.spent > b.limit) {
                statusLabel = "Limit Exceeded";
                statusColor = "red";
              } else if (percent >= 80) {
                statusLabel = "Critical (80%+)";
                statusColor = "gold";
              }
              const budgetId = b.id || `b-${b.category}`;
              const isEditing = editingBudgetId === budgetId;

              return (
                <div key={idx} style={{ padding: "12px", border: "1px solid hsl(var(--border-dim))", borderRadius: "12px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px", fontSize: "0.82rem", alignItems: "center" }}>
                    <strong style={{ textTransform: "capitalize" }}>{b.category}</strong>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span className="review-badge" style={{ backgroundColor: `hsla(var(--accent-${statusColor}), 0.1)`, color: `hsl(var(--accent-${statusColor}))`, fontSize: "0.68rem" }}>
                        {statusLabel}
                      </span>
                      {!isEditing && (
                        <>
                          <button onClick={() => { setEditingBudgetId(budgetId); setEditingBudgetLimit(b.limit); }} style={{ background: "none", border: "none", cursor: "pointer", padding: "2px" }} title="Edit limit">
                            <Edit2 size={14} color="hsl(var(--accent-blue))" />
                          </button>
                          <button onClick={() => handleDeleteBudget(budgetId)} style={{ background: "none", border: "none", cursor: "pointer", padding: "2px" }} title="Delete budget">
                            <Trash2 size={14} color="hsl(var(--accent-red))" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                  {isEditing ? (
                    <div style={{ display: "flex", gap: "8px", alignItems: "center", marginTop: "6px" }}>
                      <label style={{ fontSize: "0.78rem", color: "hsl(var(--text-secondary))" }}>Monthly Limit: ₹</label>
                      <input type="number" value={editingBudgetLimit} onChange={e => setEditingBudgetLimit(Number(e.target.value))} style={{ padding: "6px 10px", borderRadius: "8px", border: "1px solid hsl(var(--border-dim))", fontSize: "0.85rem", width: "120px" }} />
                      <button onClick={() => handleUpdateBudget(budgetId)} style={{ background: "hsl(var(--accent-green))", color: "#fff", border: "none", borderRadius: "6px", padding: "5px 12px", fontSize: "0.78rem", fontWeight: 700, cursor: "pointer" }}>Save</button>
                      <button onClick={() => setEditingBudgetId(null)} style={{ background: "none", border: "1px solid hsl(var(--border-dim))", borderRadius: "6px", padding: "5px 12px", fontSize: "0.78rem", cursor: "pointer" }}>Cancel</button>
                    </div>
                  ) : (
                    <>
                      <div className="goal-progress-bar">
                        <div className="goal-progress-fill" style={{ width: `${percent}%`, backgroundColor: `hsl(var(--accent-${statusColor}))` }}></div>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between", marginTop: "4px", fontSize: "0.75rem", color: "hsl(var(--text-muted))" }}>
                        <span>₹{b.spent.toLocaleString("en-IN")} spent</span>
                        <span>₹{b.remaining.toLocaleString("en-IN")} remaining</span>
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>

          {/* Add Budget */}
          {isAddBudgetOpen ? (
            <div style={{ marginTop: "14px", padding: "14px", border: "1px dashed hsl(var(--accent-blue))", borderRadius: "12px" }}>
              <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
                <input type="text" placeholder="Category name" value={newBudgetCategory} onChange={e => setNewBudgetCategory(e.target.value)} style={{ padding: "6px 10px", borderRadius: "8px", border: "1px solid hsl(var(--border-dim))", fontSize: "0.85rem", flex: 1, minWidth: "120px" }} />
                <input type="number" placeholder="Monthly limit" value={newBudgetLimit || ""} onChange={e => setNewBudgetLimit(Number(e.target.value))} style={{ padding: "6px 10px", borderRadius: "8px", border: "1px solid hsl(var(--border-dim))", fontSize: "0.85rem", width: "120px" }} />
                <button onClick={handleCreateBudget} style={{ background: "hsl(var(--accent-green))", color: "#fff", border: "none", borderRadius: "6px", padding: "6px 14px", fontSize: "0.78rem", fontWeight: 700, cursor: "pointer" }}>Add</button>
                <button onClick={() => setIsAddBudgetOpen(false)} style={{ background: "none", border: "1px solid hsl(var(--border-dim))", borderRadius: "6px", padding: "6px 14px", fontSize: "0.78rem", cursor: "pointer" }}>Cancel</button>
              </div>
            </div>
          ) : (
            <button onClick={() => setIsAddBudgetOpen(true)} style={{ marginTop: "14px", background: "none", border: "1px dashed hsl(var(--accent-blue))", borderRadius: "10px", padding: "10px 16px", fontSize: "0.82rem", color: "hsl(var(--accent-blue))", fontWeight: 700, cursor: "pointer", width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}>
              <Plus size={14} /> Add Budget Category
            </button>
          )}
        </div>

        {/* Dedicated Savings Goals Section */}
        <div className="premium-card">
          <h3 style={{ margin: "0 0 16px 0", fontSize: "1rem", fontWeight: 700 }}>Family Goals Progress</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {goals.map((g, index) => {
              const percent = g.target > 0 ? Math.min((g.current / g.target) * 100, 100) : 0;
              
              // Calculate months left from actual target_date
              let monthsLeft = 12;
              if (g.target_date) {
                const targetDate = new Date(g.target_date);
                const now = new Date();
                monthsLeft = Math.max(1, Math.round((targetDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24 * 30)));
              }

              const needed = g.target - g.current;
              const contribution = needed > 0 ? Math.round(needed / monthsLeft) : 0;
              const goalId = g.id || `g-${index + 1}`;
              const isEditing = editingGoalId === goalId;

              return (
                <div key={index} className="goal-item-card" style={{ padding: "14px" }}>
                  {isEditing ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                      <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
                        <input type="text" value={editingGoalData.goal_name} onChange={e => setEditingGoalData(prev => ({ ...prev, goal_name: e.target.value }))} placeholder="Goal name" style={{ padding: "6px 10px", borderRadius: "8px", border: "1px solid hsl(var(--border-dim))", fontSize: "0.85rem", flex: 1, minWidth: "130px" }} />
                        <input type="number" value={editingGoalData.target_amount || ""} onChange={e => setEditingGoalData(prev => ({ ...prev, target_amount: Number(e.target.value) }))} placeholder="Target ₹" style={{ padding: "6px 10px", borderRadius: "8px", border: "1px solid hsl(var(--border-dim))", fontSize: "0.85rem", width: "120px" }} />
                        <input type="date" value={editingGoalData.target_date} onChange={e => setEditingGoalData(prev => ({ ...prev, target_date: e.target.value }))} style={{ padding: "6px 10px", borderRadius: "8px", border: "1px solid hsl(var(--border-dim))", fontSize: "0.85rem" }} />
                      </div>
                      <div style={{ display: "flex", gap: "8px" }}>
                        <button onClick={() => handleUpdateGoal(goalId)} style={{ background: "hsl(var(--accent-green))", color: "#fff", border: "none", borderRadius: "6px", padding: "5px 14px", fontSize: "0.78rem", fontWeight: 700, cursor: "pointer" }}>Save</button>
                        <button onClick={() => setEditingGoalId(null)} style={{ background: "none", border: "1px solid hsl(var(--border-dim))", borderRadius: "6px", padding: "5px 14px", fontSize: "0.78rem", cursor: "pointer" }}>Cancel</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="goal-info" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span className="goal-name">{g.name}</span>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <span className="goal-amounts">
                            ₹{g.current.toLocaleString("en-IN")} <span>/ ₹{g.target.toLocaleString("en-IN")}</span>
                          </span>
                          <button onClick={() => { setEditingGoalId(goalId); setEditingGoalData({ goal_name: g.name, target_amount: g.target, target_date: g.target_date || "" }); }} style={{ background: "none", border: "none", cursor: "pointer", padding: "2px" }} title="Edit goal">
                            <Edit2 size={14} color="hsl(var(--accent-blue))" />
                          </button>
                          <button onClick={() => handleDeleteGoal(goalId)} style={{ background: "none", border: "none", cursor: "pointer", padding: "2px" }} title="Delete goal">
                            <Trash2 size={14} color="hsl(var(--accent-red))" />
                          </button>
                        </div>
                      </div>
                      <div className="goal-progress-bar" style={{ height: "8px", marginTop: "6px" }}>
                        <div className="goal-progress-fill" style={{ width: `${percent}%` }}></div>
                      </div>
                      <div className="goal-footer-info" style={{ marginTop: "6px" }}>
                        <span>{percent.toFixed(0)}% saved • {g.est}</span>
                        <strong style={{ color: "hsl(var(--accent-green))" }}>
                          {contribution > 0 ? `₹${contribution.toLocaleString("en-IN")}/mo needed` : "Completed!"}
                        </strong>
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>

          {/* Add Goal */}
          {isAddGoalOpen ? (
            <div style={{ marginTop: "14px", padding: "14px", border: "1px dashed hsl(var(--accent-blue))", borderRadius: "12px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
                  <input type="text" placeholder="Goal name" value={newGoalName} onChange={e => setNewGoalName(e.target.value)} style={{ padding: "6px 10px", borderRadius: "8px", border: "1px solid hsl(var(--border-dim))", fontSize: "0.85rem", flex: 1, minWidth: "130px" }} />
                  <input type="number" placeholder="Target ₹" value={newGoalTarget || ""} onChange={e => setNewGoalTarget(Number(e.target.value))} style={{ padding: "6px 10px", borderRadius: "8px", border: "1px solid hsl(var(--border-dim))", fontSize: "0.85rem", width: "120px" }} />
                  <input type="date" value={newGoalDate} onChange={e => setNewGoalDate(e.target.value)} style={{ padding: "6px 10px", borderRadius: "8px", border: "1px solid hsl(var(--border-dim))", fontSize: "0.85rem" }} />
                </div>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button onClick={handleCreateGoal} style={{ background: "hsl(var(--accent-green))", color: "#fff", border: "none", borderRadius: "6px", padding: "6px 14px", fontSize: "0.78rem", fontWeight: 700, cursor: "pointer" }}>Add</button>
                  <button onClick={() => setIsAddGoalOpen(false)} style={{ background: "none", border: "1px solid hsl(var(--border-dim))", borderRadius: "6px", padding: "6px 14px", fontSize: "0.78rem", cursor: "pointer" }}>Cancel</button>
                </div>
              </div>
            </div>
          ) : (
            <button onClick={() => setIsAddGoalOpen(true)} style={{ marginTop: "14px", background: "none", border: "1px dashed hsl(var(--accent-blue))", borderRadius: "10px", padding: "10px 16px", fontSize: "0.82rem", color: "hsl(var(--accent-blue))", fontWeight: 700, cursor: "pointer", width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}>
              <Plus size={14} /> Add Savings Goal
            </button>
          )}
        </div>
      </div>
    );
  };

  // Render Debt Center Tab Content
  const renderDebtCenter = () => {
    const activeDebtsList = transactions.filter(t => t.item_type === "debt");
    return (
      <div className="animate-fade-in">
        <h2 style={{ fontSize: "1.35rem", fontWeight: 800, marginBottom: "20px" }}>Household Debt Center</h2>

        {/* List of outstanding loans */}
        <div className="premium-card">
          <h3 style={{ margin: "0 0 16px 0", fontSize: "1rem", fontWeight: 700 }}>Outstanding Debt Obligations</h3>
          {activeDebtsList.length === 0 ? (
            <div style={{ textAlign: "center", padding: "16px", color: "hsl(var(--text-muted))" }}>
              Excellent! No outstanding debts logged in family memory.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {activeDebtsList.map((d, idx) => (
                <div key={idx} style={{ padding: "12px", border: "1px solid hsl(var(--border-dim))", borderRadius: "12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <strong style={{ display: "block", fontSize: "0.9rem" }}>{d.description}</strong>
                    <span style={{ fontSize: "0.78rem", color: "hsl(var(--text-secondary))" }}>
                      Borrower: {d.borrower_name || d.logged_by} • Lender: {d.lender_name}
                    </span>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <span style={{ fontSize: "1rem", fontWeight: 800, color: "hsl(var(--accent-red))" }}>₹{d.amount.toLocaleString("en-IN")}</span>
                    <span className="review-badge" style={{ display: "block", marginTop: "4px", backgroundColor: "hsla(var(--accent-red), 0.08)", color: "hsl(var(--accent-red))", fontSize: "0.65rem", padding: "1px 6px" }}>
                      Active Obligation
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Debt prioritization advisor */}
        <div className="premium-card" style={{ borderLeft: "4px solid hsl(var(--accent-red))", backgroundColor: "hsla(var(--accent-red), 0.01)" }}>
          <h3 style={{ margin: "0 0 8px 0", fontSize: "0.95rem", fontWeight: 700, color: "hsl(var(--accent-red))" }}>Debt Reduction Prioritization</h3>
          <p style={{ fontSize: "0.85rem", color: "hsl(var(--text-secondary))", margin: "0 0 12px 0" }}>
            Based on active entries in the {familyName} financial memory, we recommend the following repayment optimization strategy:
          </p>
          <div style={{ padding: "12px", borderRadius: "10px", backgroundColor: "#ffffff", border: "1px solid hsl(var(--border-dim))" }}>
            <strong style={{ fontSize: "0.85rem", display: "block", marginBottom: "4px" }}>Avalanche Repayment Strategy:</strong>
            <ul style={{ fontSize: "0.8rem", color: "hsl(var(--text-secondary))", paddingLeft: "16px", lineHeight: 1.5 }}>
              <li>Prioritize paying off loans with near-term due dates first to avoid delinquency and family friction.</li>
              <li>Consolidate helper or hand-loan balances into a single sweep on payday.</li>
              <li>Utilize emergency fund allocations to pay down high-interest external debts rather than letting them compound.</li>
            </ul>
          </div>
        </div>
      </div>
    );
  };

  // Render ChatGPT-style text-only Family Assistant
    const renderAssistant = () => {
    return (
      <div className="animate-fade-in">
        <h2 style={{ fontSize: "1.35rem", fontWeight: 800, marginBottom: "20px" }}>Voice Assistant Control Center</h2>

        {/* Premium Active Calling Card */}
        <div className="premium-card" style={{ padding: "24px", background: "linear-gradient(135deg, hsla(var(--accent-green), 0.15) 0%, hsla(var(--accent-blue), 0.05) 100%)", borderLeft: "4px solid hsl(var(--accent-green))", borderRadius: "16px", marginBottom: "24px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div style={{ padding: "12px", background: "hsl(var(--bg-card))", borderRadius: "12px", color: "hsl(var(--accent-green))", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
              <Mic size={28} />
            </div>
            <div>
              <span style={{ fontSize: "0.72rem", textTransform: "uppercase", fontWeight: 800, color: "hsl(var(--text-muted))", letterSpacing: "0.05em" }}>Inbound Telephony Live</span>
              <h3 style={{ margin: "2px 0 6px 0", fontSize: "1.35rem", fontWeight: 800, color: "hsl(var(--text-primary))" }}>+91 92621 71465</h3>
              <p style={{ margin: 0, fontSize: "0.82rem", color: "hsl(var(--text-secondary))", lineHeight: "1.4" }}>
                Call this number from any registered family phone line to log expenses, check budgets, or get financial guidance.
              </p>
            </div>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px", marginBottom: "24px" }}>
          {/* Outbound Caller Trigger */}
          <div className="premium-card" style={{ display: "flex", flexDirection: "column", gap: "16px", padding: "20px" }}>
            <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 800, display: "flex", alignItems: "center", gap: "8px" }}>
              <PhoneCall size={16} color="hsl(var(--accent-blue))" />
              <span>Trigger Outbound Companion Call</span>
            </h3>
            <p style={{ margin: 0, fontSize: "0.8rem", color: "hsl(var(--text-secondary))" }}>
              Ring a family member's phone using Bolna's outgoing voice assistant.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "4px" }}>
              <label style={{ fontSize: "0.72rem", fontWeight: 700, textTransform: "uppercase", color: "hsl(var(--text-muted))" }}>Select Family Member</label>
              <select 
                className="form-input" 
                value={simSpeaker} 
                onChange={(e) => setSimSpeaker(e.target.value)}
                style={{ fontSize: "0.85rem", padding: "10px" }}
              >
                {members.map((m, idx) => (
                  <option key={idx} value={m.name}>
                    {m.name} ({m.role}) - {m.phone_number || "+91 92621 71465"}
                  </option>
                ))}
              </select>

              {(() => {
                const selectedMem = members.find(m => m.name === simSpeaker) || members[0];
                const phone = selectedMem?.phone_number || "+919262171465";
                return (
                  <button 
                    onClick={() => triggerOutboundCall(phone, simSpeaker)}
                    className="btn-submit"
                    style={{ marginTop: "8px", background: "hsl(var(--accent-blue))", color: "#ffffff", padding: "10px 16px", borderRadius: "8px", fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}
                  >
                    <PhoneCall size={14} />
                    <span>Call {simSpeaker} now</span>
                  </button>
                );
              })()}
            </div>
          </div>

          {/* Quick Guide */}
          <div className="premium-card" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
            <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 800, display: "flex", alignItems: "center", gap: "8px" }}>
              <Sparkles size={16} color="hsl(var(--accent-green))" />
              <span>Voice Interaction Quick Guide</span>
            </h3>
            <p style={{ margin: 0, fontSize: "0.8rem", color: "hsl(var(--text-secondary))" }}>
              The voice assistant responds to natural language queries. Try calling and speaking:
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "0.78rem" }}>
              <div style={{ background: "hsl(var(--bg-card-subtle))", padding: "8px 12px", borderRadius: "8px", border: "1px solid hsl(var(--border-dim))" }}>
                <strong>Logging:</strong> &ldquo;I spent 1200 rupees on groceries today&rdquo;
              </div>
              <div style={{ background: "hsl(var(--bg-card-subtle))", padding: "8px 12px", borderRadius: "8px", border: "1px solid hsl(var(--border-dim))" }}>
                <strong>Budget status:</strong> &ldquo;How much remaining budget do we have for fuel?&rdquo;
              </div>
              <div style={{ background: "hsl(var(--bg-card-subtle))", padding: "8px 12px", borderRadius: "8px", border: "1px solid hsl(var(--border-dim))" }}>
                <strong>Education:</strong> &ldquo;Explain compound interest and safe savings options&rdquo;
              </div>
            </div>
          </div>
        </div>

        {/* Live Timeline of Voice Interactions (Embedded) */}
        <div>
          <h3 style={{ fontSize: "1.05rem", fontWeight: 800, marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
            <List size={18} />
            <span>Recent Voice Conversations</span>
          </h3>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {timeline.length === 0 ? (
              <div className="premium-card" style={{ textAlign: "center", padding: "32px" }}>
                <Volume2 size={24} style={{ color: "hsl(var(--text-muted))", marginBottom: "6px" }} />
                <p style={{ margin: 0, fontWeight: 700 }}>No call logs found</p>
                <p style={{ margin: "4px 0 0 0", fontSize: "0.82rem", color: "hsl(var(--text-muted))" }}>Calls placed to the Bolna phone line will appear here.</p>
              </div>
            ) : (
              timeline.slice(0, 5).map((call, idx) => {
                const dateObj = new Date(call.created_at);
                const dateText = dateObj.toLocaleDateString([], { month: "short", day: "numeric" }) + " • " + dateObj.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
                
                const isExpense = !!call.extracted_json?.expense;
                const isDebt = !!call.extracted_json?.debt;
                const toolName = isExpense ? "record-expense" : isDebt ? "record-debt" : "get-literacy";

                return (
                  <div key={idx} className="premium-card" style={{ padding: "16px", marginBottom: "0" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span className="review-badge" style={{ backgroundColor: "hsla(var(--accent-green), 0.1)", color: "hsl(var(--accent-green))" }}>
                          Call Log
                        </span>
                        <span style={{ fontSize: "0.78rem", fontWeight: 700 }}>{call.members?.name || "Ramesh"}</span>
                      </div>
                      <span style={{ fontSize: "0.72rem", color: "hsl(var(--text-muted))" }}>{dateText}</span>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "6px", margin: "0 0 10px 0", paddingLeft: "8px", borderLeft: "2px solid hsl(var(--border-dim))" }}>
                      {Array.isArray(call.transcript) ? (
                        call.transcript.map((turn: any, tIdx: number) => (
                          <div key={tIdx} style={{ fontSize: "0.82rem", lineHeight: "1.35" }}>
                            <span style={{ fontWeight: 600, textTransform: "capitalize", color: turn.role === "user" ? "hsl(var(--accent-blue))" : "hsl(var(--text-secondary))" }}>
                              {turn.role || "user"}:
                            </span>{" "}
                            <span style={{ color: "hsl(var(--text-secondary))" }}>{turn.content}</span>
                          </div>
                        ))
                      ) : (
                        <p style={{ fontSize: "0.85rem", fontStyle: "italic", margin: 0 }}>
                          &ldquo;{String(call.transcript)}&rdquo;
                        </p>
                      )}
                    </div>

                    <div style={{ display: "flex", gap: "12px", borderTop: "1px solid hsl(var(--border-dim))", paddingTop: "10px", flexWrap: "wrap", fontSize: "0.74rem" }}>
                      <span>Language: <strong style={{ textTransform: "capitalize" }}>{call.language || "English"}</strong></span>
                      <span>Confidence: <strong>{((call.confidence || 0.9) * 100).toFixed(0)}%</strong></span>
                      <span>Tool Executed: <code style={{ backgroundColor: "hsl(var(--bg-card-subtle))", padding: "2px 4px", borderRadius: "4px" }}>{toolName}</code></span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    );
  };;

  // Render Voice Logs Content
  const renderVoiceLogs = () => {
    return (
      <div className="animate-fade-in">
        <h2 style={{ fontSize: "1.35rem", fontWeight: 800, marginBottom: "20px" }}>Bolna Voice Interaction Logs</h2>

        <div className="premium-card" style={{ padding: "16px", marginBottom: "20px", display: "flex", gap: "12px", alignItems: "center", borderLeft: "4px solid hsl(var(--accent-green))" }}>
          <PhoneCall size={20} color="hsl(var(--accent-green))" />
          <div>
            <strong style={{ fontSize: "0.88rem", display: "block" }}>Outbound Calling Enabled</strong>
            <p style={{ margin: "2px 0 0 0", fontSize: "0.78rem", color: "hsl(var(--text-secondary))" }}>
              Parents can speak naturally to the inbound phone line <strong>+91 92621 71465</strong> to log transactions.
            </p>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {timeline.length === 0 ? (
            <div className="premium-card" style={{ textAlign: "center", padding: "32px" }}>
              <Volume2 size={24} style={{ color: "hsl(var(--text-muted))", marginBottom: "6px" }} />
              <p style={{ margin: 0, fontWeight: 700 }}>No call logs found</p>
              <p style={{ margin: "4px 0 0 0", fontSize: "0.82rem", color: "hsl(var(--text-muted))" }}>Calls placed to the Bolna phone line will appear here.</p>
            </div>
          ) : (
            timeline.map((call, idx) => {
              const dateObj = new Date(call.created_at);
              const dateText = dateObj.toLocaleDateString([], { month: "short", day: "numeric" }) + " • " + dateObj.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
              
              // Extract tools info
              const isExpense = !!call.extracted_json?.expense;
              const isDebt = !!call.extracted_json?.debt;
              const toolName = isExpense ? "record-expense" : isDebt ? "record-debt" : "get-literacy";

              return (
                <div key={idx} className="premium-card" style={{ padding: "16px", marginBottom: "0" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span className="review-badge" style={{ backgroundColor: "hsla(var(--accent-green), 0.1)", color: "hsl(var(--accent-green))" }}>
                        Call Log
                      </span>
                      <span style={{ fontSize: "0.78rem", fontWeight: 700 }}>{call.members?.name || "Ramesh"}</span>
                    </div>
                    <span style={{ fontSize: "0.72rem", color: "hsl(var(--text-muted))" }}>{dateText}</span>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "6px", margin: "0 0 10px 0", paddingLeft: "8px", borderLeft: "2px solid hsl(var(--border-dim))" }}>
                    {Array.isArray(call.transcript) ? (
                      call.transcript.map((turn: any, tIdx: number) => (
                        <div key={tIdx} style={{ fontSize: "0.82rem", lineHeight: "1.35" }}>
                          <span style={{ fontWeight: 600, textTransform: "capitalize", color: turn.role === "user" ? "hsl(var(--accent-blue))" : "hsl(var(--text-secondary))" }}>
                            {turn.role || "user"}:
                          </span>{" "}
                          <span style={{ color: "hsl(var(--text-secondary))" }}>{turn.content}</span>
                        </div>
                      ))
                    ) : (
                      <p style={{ fontSize: "0.85rem", fontStyle: "italic", margin: 0 }}>
                        &ldquo;{String(call.transcript)}&rdquo;
                      </p>
                    )}
                  </div>

                  <div style={{ display: "flex", gap: "12px", borderTop: "1px solid hsl(var(--border-dim))", paddingTop: "10px", flexWrap: "wrap", fontSize: "0.74rem" }}>
                    <span>Language: <strong style={{ textTransform: "capitalize" }}>{call.language || "English"}</strong></span>
                    <span>Confidence: <strong>{((call.confidence || 0.9) * 100).toFixed(0)}%</strong></span>
                    <span>Tool Executed: <code style={{ backgroundColor: "hsl(var(--bg-card-subtle))", padding: "2px 4px", borderRadius: "4px" }}>{toolName}</code></span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    );
  };

  // Render Household Profiles Tab
  const renderProfiles = () => {
    return (
      <div className="animate-fade-in">
        <h2 style={{ fontSize: "1.35rem", fontWeight: 800, marginBottom: "20px" }}>Household Profiles & Danger Zone</h2>

        <div className="premium-card" style={{ marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h3 className="sub-title" style={{ marginBottom: "4px" }}>Global Family Name</h3>
            <p style={{ fontSize: "0.85rem", color: "hsl(var(--text-secondary))", margin: 0 }}>This name appears across your dashboard and logs.</p>
          </div>
          <div>
            {isEditingFamilyName ? (
              <div style={{ display: "flex", gap: "8px" }}>
                <input
                  type="text"
                  value={editFamilyNameValue}
                  onChange={(e) => setEditFamilyNameValue(e.target.value)}
                  className="input-field"
                  style={{ width: "200px" }}
                  placeholder="Enter Family Name"
                />
                <button 
                  className="primary-button" 
                  onClick={handleUpdateFamilyName}
                  style={{ padding: "8px 16px", borderRadius: "8px" }}
                >
                  Save
                </button>
                <button 
                  className="secondary-button" 
                  onClick={() => setIsEditingFamilyName(false)}
                  style={{ padding: "8px 16px", borderRadius: "8px" }}
                >
                  Cancel
                </button>
              </div>
            ) : (
              <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                <strong style={{ fontSize: "1.1rem" }}>{familyName}</strong>
                <button 
                  className="action-icon-button"
                  onClick={() => {
                    setEditFamilyNameValue(familyName);
                    setIsEditingFamilyName(true);
                  }}
                  title="Edit Family Name"
                >
                  <Pencil size={16} />
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="member-grid">
          {members.map((m, idx) => (
            <div key={idx} className="member-card" onClick={() => triggerEditMember(m)} style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: "12px", border: "1px solid hsl(var(--border-dim))", borderRadius: "16px", padding: "20px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px", width: "100%" }}>
                <div className="member-avatar-box">
                  {m.name[0]}
                </div>
                <div>
                  <h4 style={{ margin: 0, fontSize: "1rem", fontWeight: 700 }}>{m.name}</h4>
                  <span style={{ fontSize: "0.78rem", color: "hsl(var(--text-muted))" }}>
                    {m.role}
                  </span>
                </div>
              </div>
              <div style={{ width: "100%", borderTop: "1px solid hsl(var(--border-dim))", paddingTop: "12px", marginTop: "4px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", marginBottom: "6px" }}>
                  <span style={{ color: "hsl(var(--text-secondary))" }}>Language Preference:</span>
                  <strong>{m.language}</strong>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", marginBottom: "6px" }}>
                  <span style={{ color: "hsl(var(--text-secondary))" }}>Phone Number:</span>
                  <strong>{m.phone_number || "+91 92621 71465"}</strong>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem" }}>
                  <span style={{ color: "hsl(var(--text-secondary))" }}>Interaction Style:</span>
                  <strong>{m.voice ? "Voice Calls" : "Dashboard UI"}</strong>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="premium-card" style={{ marginTop: "24px" }}>
          <h3 className="sub-title">Household Shared Calling</h3>
          <p style={{ fontSize: "0.85rem", color: "hsl(var(--text-secondary))", marginBottom: "12px" }}>
            All family members share the main landline / phone number. The Bolna telephony system resolves caller identities dynamically:
          </p>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", background: "hsl(var(--bg-card-subtle))", padding: "8px 16px", borderRadius: "8px", fontWeight: 700 }}>
            <PhoneCall size={14} color="hsl(var(--accent-green))" />
            <span>+91 92621 71465</span>
          </div>
        </div>

        {/* Danger Zone: Reset Data */}
        <div className="premium-card" style={{ marginTop: "24px", border: "1.5px solid hsla(var(--accent-red), 0.2)" }}>
          <h3 className="sub-title" style={{ color: "hsl(var(--accent-red))" }}>Danger Zone</h3>
          <p style={{ fontSize: "0.85rem", color: "hsl(var(--text-secondary))", marginBottom: "16px" }}>
            Reset family financial database. Clears transactions, debts, voice logs, and memory tables.
          </p>
          <button 
            onClick={handleResetData}
            className="btn-review discard"
            style={{ padding: "10px 16px", borderRadius: "8px", fontWeight: "700" }}
          >
            Reset Family Memory Database
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="app-container">
      {/* Desktop left sidebar */}
      <aside className="desktop-sidebar">
        <div>
          <div className="sidebar-logo">
            <div className="sidebar-logo">
              <div className="logo-icon">
                <Volume2 size={18} />
              </div>
              <span className="logo-text">Family Memory OS</span>
            </div>
          </div>

          <nav className="sidebar-menu">
            <button 
              className={`menu-item ${activeTab === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveTab('overview')}
            >
              <Home size={18} />
              <span>Overview</span>
            </button>
            <button 
              className={`menu-item ${activeTab === 'ledger' ? 'active' : ''}`}
              onClick={() => setActiveTab('ledger')}
            >
              <List size={18} />
              <span>Ledger</span>
            </button>
            <button 
              className={`menu-item ${activeTab === 'budgets' ? 'active' : ''}`}
              onClick={() => setActiveTab('budgets')}
            >
              <Wallet size={18} />
              <span>Budgets & Goals</span>
            </button>
            <button 
              className={`menu-item ${activeTab === 'debts' ? 'active' : ''}`}
              onClick={() => setActiveTab('debts')}
            >
              <Percent size={18} />
              <span>Debt Center</span>
            </button>
            <button 
              className={`menu-item ${activeTab === 'assistant' ? 'active' : ''}`}
              onClick={() => setActiveTab('assistant')}
            >
              <Sparkles size={18} />
              <span>Family Assistant</span>
            </button>
            <button 
              className={`menu-item ${activeTab === 'voice_logs' ? 'active' : ''}`}
              onClick={() => setActiveTab('voice_logs')}
            >
              <PhoneCall size={18} />
              <span>Voice Logs</span>
            </button>
            <button 
              className={`menu-item ${activeTab === 'profiles' ? 'active' : ''}`}
              onClick={() => setActiveTab('profiles')}
            >
              <Users size={18} />
              <span>Profiles</span>
            </button>
          </nav>
        </div>

        <div style={{ fontSize: "0.75rem", color: "hsl(var(--text-muted))", fontWeight: 600 }}>
          <span>{familyName} OS v1.0</span>
        </div>
      </aside>

      {/* Main Content Pane Router */}
      <main className="main-content">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'ledger' && renderLedger()}
        {activeTab === 'budgets' && renderBudgetsAndGoals()}
        {activeTab === 'debts' && renderDebtCenter()}
        {activeTab === 'assistant' && renderAssistant()}
        {activeTab === 'voice_logs' && renderVoiceLogs()}
        {activeTab === 'profiles' && renderProfiles()}
      </main>

      {/* Mobile Bottom Tab Bar */}
      <nav className="mobile-bottom-nav">
        <button 
          className={`mobile-tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <Home size={22} />
          <span>Overview</span>
        </button>
        <button 
          className={`mobile-tab-btn ${activeTab === 'ledger' ? 'active' : ''}`}
          onClick={() => setActiveTab('ledger')}
        >
          <List size={22} />
          <span>Ledger</span>
        </button>
        <button 
          className={`mobile-tab-btn center-btn ${activeTab === 'assistant' ? 'active' : ''}`}
          onClick={() => setActiveTab('assistant')}
        >
          <div className="mic-circle" style={{ backgroundColor: "hsl(var(--accent-green))", color: "#ffffff" }}>
            <Sparkles size={24} />
          </div>
        </button>
        <button 
          className={`mobile-tab-btn ${activeTab === 'budgets' ? 'active' : ''}`}
          onClick={() => setActiveTab('budgets')}
        >
          <Wallet size={22} />
          <span>Budgets</span>
        </button>
        <button 
          className={`mobile-tab-btn ${activeTab === 'debts' ? 'active' : ''}`}
          onClick={() => setActiveTab('debts')}
        >
          <Percent size={22} />
          <span>Debts</span>
        </button>
      </nav>

      {/* MODAL: Unified Add Transaction */}
      {isAddTransactionOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header" style={{ marginBottom: "12px" }}>
              <span className="modal-title">Record Transaction</span>
              <button className="close-btn" onClick={() => setIsAddTransactionOpen(false)}>
                <X size={18} />
              </button>
            </div>

            {/* Selector Tab Bar inside Modal */}
            <div style={{ display: "flex", background: "hsl(var(--bg-card-subtle))", padding: "4px", borderRadius: "8px", marginBottom: "20px" }}>
              <button 
                type="button" 
                onClick={() => setAddTxType("expense")}
                style={{ flex: 1, border: "none", background: addTxType === "expense" ? "#ffffff" : "transparent", color: addTxType === "expense" ? "hsl(var(--text-primary))" : "hsl(var(--text-secondary))", padding: "6px", borderRadius: "6px", fontSize: "0.8rem", fontWeight: 700, cursor: "pointer", transition: "all 0.2s" }}
              >
                Expense Log
              </button>
              <button 
                type="button" 
                onClick={() => setAddTxType("debt")}
                style={{ flex: 1, border: "none", background: addTxType === "debt" ? "#ffffff" : "transparent", color: addTxType === "debt" ? "hsl(var(--text-primary))" : "hsl(var(--text-secondary))", padding: "6px", borderRadius: "6px", fontSize: "0.8rem", fontWeight: 700, cursor: "pointer", transition: "all 0.2s" }}
              >
                Debt Record
              </button>
            </div>

            {addTxType === "expense" ? (
              <form onSubmit={handleAddExpense}>
                <div className="form-group">
                  <label>Amount (₹)</label>
                  <input 
                    type="number" 
                    className="form-input" 
                    placeholder="e.g. 500" 
                    required
                    value={expAmount || ""}
                    onChange={(e) => setExpAmount(parseFloat(e.target.value) || 0)}
                  />
                </div>

                <div className="form-group">
                  <label>Category</label>
                  <select 
                    className="form-input"
                    value={expCategory}
                    onChange={(e) => setExpCategory(e.target.value)}
                  >
                    <option value="groceries">Groceries</option>
                    <option value="utilities">Utilities</option>
                    <option value="fuel">Fuel</option>
                    <option value="tuition">Tuition</option>
                    <option value="misc">Miscellaneous</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Description</label>
                  <input 
                    type="text" 
                    className="form-input" 
                    placeholder="What was this spent on?"
                    value={expDesc}
                    onChange={(e) => setExpDesc(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Logged By</label>
                  <select 
                    className="form-input"
                    value={expSpeaker}
                    onChange={(e) => setExpSpeaker(e.target.value)}
                  >
                    {members.map((m, idx) => (
                      <option key={idx} value={m.name}>{m.name}</option>
                    ))}
                  </select>
                </div>

                <button type="submit" className="btn-submit" style={{ marginTop: "8px" }}>
                  Record Expense
                </button>
              </form>
            ) : (
              <form onSubmit={handleAddDebt}>
                <div className="form-group">
                  <label>Amount (₹)</label>
                  <input 
                    type="number" 
                    className="form-input" 
                    placeholder="e.g. 2000" 
                    required
                    value={debtAmount || ""}
                    onChange={(e) => setDebtAmount(parseFloat(e.target.value) || 0)}
                  />
                </div>

                <div className="form-group">
                  <label>Lender (Who lent the money)</label>
                  <input 
                    type="text" 
                    className="form-input" 
                    placeholder="Lender name" 
                    required
                    value={debtLender}
                    onChange={(e) => setDebtLender(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Borrower (Who owes the money)</label>
                  <input 
                    type="text" 
                    className="form-input" 
                    placeholder="Borrower name" 
                    required
                    value={debtBorrower}
                    onChange={(e) => setDebtBorrower(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Repayment Due Date</label>
                  <input 
                    type="date" 
                    className="form-input" 
                    value={debtDueDate}
                    onChange={(e) => setDebtDueDate(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Note / Description</label>
                  <input 
                    type="text" 
                    className="form-input" 
                    placeholder="What was this loan for?"
                    value={debtNote}
                    onChange={(e) => setDebtNote(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Logged By</label>
                  <select 
                    className="form-input"
                    value={debtSpeaker}
                    onChange={(e) => setDebtSpeaker(e.target.value)}
                  >
                    {members.map((m, idx) => (
                      <option key={idx} value={m.name}>{m.name}</option>
                    ))}
                  </select>
                </div>

                <button type="submit" className="btn-submit" style={{ marginTop: "8px" }}>
                  Save Debt Record
                </button>
              </form>
            )}
          </div>
        </div>
      )}

      {/* MODAL: Edit Family Member details */}
      {isEditMemberOpen && editingMember && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <span className="modal-title">Edit Member: {editingMember.name}</span>
              <button className="close-btn" onClick={() => setIsEditMemberOpen(false)}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleEditMember}>
              <div className="form-group">
                <label>Family Role</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={memberRole}
                  onChange={(e) => setMemberRole(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Phone Number</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={memberPhone}
                  onChange={(e) => setMemberPhone(e.target.value)}
                  placeholder="+919876543210"
                />
              </div>

              <div className="form-group">
                <label>Preferred Language</label>
                <select 
                  className="form-input"
                  value={memberLang}
                  onChange={(e) => setMemberLang(e.target.value)}
                >
                  <option value="English">English</option>
                  <option value="Hindi">Hindi</option>
                  <option value="Tamil">Tamil</option>
                  <option value="Malayalam">Malayalam</option>
                  <option value="Telugu">Telugu</option>
                </select>
              </div>

              <div className="form-group" style={{ flexDirection: "row", alignItems: "center", gap: "10px" }}>
                <input 
                  type="checkbox" 
                  id="voice_check"
                  checked={memberVoice}
                  style={{ width: "16px", height: "16px", cursor: "pointer" }}
                  onChange={(e) => setMemberVoice(e.target.checked)}
                />
                <label htmlFor="voice_check" style={{ cursor: "pointer", textTransform: "none" }}>Voice assistant interaction enabled</label>
              </div>

              <button type="submit" className="btn-submit" style={{ marginTop: "12px" }}>
                Save Profile Updates
              </button>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Edit Transaction */}
      {editingTransaction && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <span className="modal-title">
                Edit {editingTransaction.item_type === "expense" ? "Expense" : "Debt Record"}
              </span>
              <button className="close-btn" onClick={() => setEditingTransaction(null)}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleSaveEdit}>
              <div className="form-group">
                <label>Amount (₹)</label>
                <input 
                  type="number" 
                  className="form-input" 
                  required
                  value={editTxAmount || ""}
                  onChange={(e) => setEditTxAmount(parseFloat(e.target.value) || 0)}
                />
              </div>

              {editingTransaction.item_type === "expense" ? (
                <div className="form-group">
                  <label>Category</label>
                  <select 
                    className="form-input"
                    value={editTxCategory}
                    onChange={(e) => setEditTxCategory(e.target.value)}
                  >
                    <option value="groceries">Groceries</option>
                    <option value="utilities">Utilities</option>
                    <option value="fuel">Fuel</option>
                    <option value="tuition">Tuition</option>
                    <option value="misc">Miscellaneous</option>
                  </select>
                </div>
              ) : (
                <>
                  <div className="form-group">
                    <label>Lender</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      required
                      value={editTxLender}
                      onChange={(e) => setEditTxLender(e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Borrower</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      required
                      value={editTxBorrower}
                      onChange={(e) => setEditTxBorrower(e.target.value)}
                    />
                  </div>
                </>
              )}

              <div className="form-group">
                <label>Description / Note</label>
                <input 
                  type="text" 
                  className="form-input" 
                  required
                  value={editTxDesc}
                  onChange={(e) => setEditTxDesc(e.target.value)}
                />
              </div>

              <button type="submit" className="btn-submit" style={{ marginTop: "8px" }}>
                Save Changes
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
