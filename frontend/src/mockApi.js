export const mockDb = {
  decisions: [],
  rules: {
    current_rule: { risk_threshold: 0.40, min_income: 15000, watchlist_enabled: true },
    history: []
  }
};

export const apiFetch = async (url, options = {}) => {
  const method = options.method || 'GET';
  // Remove the API_BASE part (http://localhost:8000)
  const urlObj = new URL(url.startsWith('http') ? url : `http://localhost:8000${url}`);
  const path = urlObj.pathname;
  const body = options.body ? JSON.parse(options.body) : null;

  const jsonResponse = (data) => Promise.resolve({ json: () => Promise.resolve(data) });

  if (path === '/metrics') {
    const total = mockDb.decisions.length;
    const approved = mockDb.decisions.filter(d => d.decision === 'APPROVE').length;
    return jsonResponse({
        total_applications: total,
        approved_count: approved,
        rejected_count: total - approved,
        approval_rate: total > 0 ? (approved / total * 100).toFixed(1) : 0,
        model_auc: 0.842,
        fairness_multiplier: 0.921,
        replay_match_rate: 100.0,
        avg_latency_seconds: 0.14
    });
  }
  if (path === '/api/decisions') {
    return jsonResponse(mockDb.decisions);
  }
  if (path === '/api/rules') {
    if (method === 'POST') {
      mockDb.rules.current_rule = body;
      return jsonResponse({ message: "New rule version deployed successfully.", current_rule: body });
    }
    return jsonResponse(mockDb.rules);
  }
  if (path === '/api/fairness') {
    return jsonResponse({
        model_auc: 0.842,
        fairness_multiplier: 0.921,
        overall_score: 0.775,
        groups: [
            {group: "Group A (Primary)", selection_rate: 64.2, tpr: 0.86, fpr: 0.12},
            {group: "Group B (Thin-File)", selection_rate: 61.8, tpr: 0.84, fpr: 0.13},
            {group: "Group C (Gig/Rural)", selection_rate: 59.5, tpr: 0.82, fpr: 0.14}
        ]
    });
  }
  if (path === '/api/proxy-check') {
    return jsonResponse([
        {feature: "Gig Earnings Level", correlation: 0.12, risk: "LOW (Safe)", status: "PERMITTED"},
        {feature: "Rent Payment Timeliness", correlation: 0.08, risk: "LOW (Safe)", status: "PERMITTED"},
        {feature: "Telecom Payment History", correlation: 0.05, risk: "LOW (Safe)", status: "PERMITTED"},
        {feature: "Device Type Score", correlation: 0.68, risk: "HIGH (Proxy Risk)", status: "RESTRICTED"},
        {feature: "Social Connections Count", correlation: 0.74, risk: "HIGH (Proxy Risk)", status: "PROHIBITED"}
    ]);
  }
  if (path === '/api/simulate-h8') {
    return jsonResponse({
      prohibited_features: body.prohibited_features,
      new_model_version: "v1.2.0-h8-retrained",
      total_historical_replayed: mockDb.decisions.length,
      affected_count: 0,
      affected_applications: [],
      remediation_plan: "Generate compliance review notification and offer non-penalizing re-assessment."
    });
  }
  if (path === '/api/assess') {
    const input = body;
    let clean_rent = Math.min(100, Math.max(0, input.rent_payment_ratio));
    let score = (
        ((input.monthly_income - input.monthly_expense) / 10000) * 0.2 +
        (clean_rent / 100) * 2.5 +
        (input.utility_payment_ratio / 100) * 1.5 +
        (input.telecom_payment_ratio / 100) * 1.0 +
        input.cash_flow_stability * 2.0 +
        (input.gig_income / 5000) * 0.5 +
        input.platform_rating * 0.8
    );
    let risk_prob = 1 / (1 + Math.exp(score - 7.5));
    let risk_score = Math.floor((1.0 - risk_prob) * 100);

    let watchlist = ["JOHN DOE", "SANCTIONS_USER_01", "FRAUD_TEST_99", "CRIMINAL_RECORD_X", "BAD_ACTOR_007"];
    let isFlagged = watchlist.includes((input.applicant_name || "").toUpperCase().trim());
    let wl_res = mockDb.rules.current_rule.watchlist_enabled ? (isFlagged ? "MATCH (FLAGGED)" : "CLEAR") : "BYPASSED";
    
    let decision = "APPROVE";
    let reasons = [];
    if (wl_res === "MATCH (FLAGGED)") { decision = "REJECT"; reasons.push("Applicant flagged on regulatory watchlist screening."); }
    if (input.monthly_income < mockDb.rules.current_rule.min_income) { decision = "REJECT"; reasons.push(`Monthly income (₹${input.monthly_income}) below minimum policy threshold.`); }
    if (risk_prob > mockDb.rules.current_rule.risk_threshold) { decision = "REJECT"; reasons.push(`Predicted default risk (${risk_prob.toFixed(2)}) exceeds policy safety limit.`); }
    
    if (decision === "REJECT" && reasons.length === 0) {
        if (risk_prob > 0.35) reasons.push("High predicted repayment default risk score.");
        if (input.cash_flow_stability < 0.6) reasons.push("Unstable recent bank cash flow volatility.");
    }
    
    if (decision === "APPROVE") {
       reasons.push("Satisfactory credit profile and alternate data metrics.");
    }

    let result = {
        application_id: "APP-" + Math.floor(Math.random()*100000).toString().padStart(5, '0'),
        applicant_name: input.applicant_name,
        decision: decision,
        risk_score: risk_score,
        risk_prob: risk_prob,
        watchlist_result: wl_res,
        reasons: reasons.slice(0,4),
        attribution: [
            {feature: "Rent Payment Timeliness", impact: parseFloat(((clean_rent - 80) * 0.15).toFixed(2))},
            {feature: "Utility History", impact: parseFloat(((input.utility_payment_ratio - 80) * 0.1).toFixed(2))},
            {feature: "Cash Flow Stability", impact: parseFloat(((input.cash_flow_stability - 0.5) * 18).toFixed(2))},
            {feature: "Net Buffer", impact: parseFloat((((input.monthly_income - input.monthly_expense) - 10000) / 5000).toFixed(2))},
            {feature: "Gig Earnings", impact: parseFloat((input.gig_income / 4000).toFixed(2))}
        ],
        warnings: [],
        hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        model_version: "v1.2.0",
        rule_version: 1,
        latency_seconds: 0.082,
        input_data: input,
        timestamp: new Date().toISOString()
    };
    mockDb.decisions.unshift(result); 
    return jsonResponse(result);
  }
  if (path.startsWith('/api/replay/')) {
    const appId = path.split('/').pop();
    const orig = mockDb.decisions.find(d => d.application_id === appId);
    if (!orig) return Promise.reject(new Error("Not found"));
    return jsonResponse({
        application_id: appId,
        original_record: orig,
        replayed_outcome: {
            decision: orig.decision,
            risk_score: orig.risk_score,
            risk_prob: orig.risk_prob,
            model_version: orig.model_version,
            rule_version: orig.rule_version
        },
        is_byte_match: true,
        match_percentage: 100.0,
        execution_time_sec: 0.04
    });
  }

  return Promise.reject(new Error("Not found"));
};
