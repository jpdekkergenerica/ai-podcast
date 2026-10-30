import React from "react";
import { BlockCursor } from "../ai/BlockCursor.jsx";
import { Chip } from "../core/Chip.jsx";
import { formatMoney } from "../money/Amount.jsx";

function fmtExpr(expr) {
  return expr.replace(/\d+/g, (d) => String(parseInt(d, 10)).replace(/\B(?=(\d{3})+(?!\d))/g, "."));
}

/** Entry-screen amount readout in Geist Pixel. Shows the running expression and its result. */
export function AmountField({ expression = "", kind = "expense", currency = "VND", focused = true, error, label = "Số tiền", style }) {
  const hasOp = /[+−×÷]/.test(expression);
  let result = null;
  if (hasOp) { try { result = evalExpr(expression); } catch (e) { result = null; } }
  const sign = kind === "income" ? "+" : kind === "expense" ? "\u2212" : "";
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8, padding: "16px 16px 12px", borderBottom: (focused || error ? "var(--border-2)" : "var(--border-1)") + " solid var(--border-strong)", ...style }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ font: "var(--type-label)", color: "var(--text-secondary)" }}>{label}</span>
        {currency !== "VND" && <Chip variant="code">{currency}</Chip>}
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, minHeight: 44, overflow: "hidden" }}>
        <span style={{ font: "var(--type-display-l)", color: expression ? "var(--text-primary)" : "var(--text-tertiary)", whiteSpace: "nowrap" }}>
          {expression ? sign + fmtExpr(expression) : "0"}
        </span>
        {focused && <BlockCursor width={12} height={36} />}
        <span style={{ font: "var(--type-display-s)", color: "var(--text-secondary)", marginLeft: "auto" }}>{currency === "VND" ? "₫" : ""}</span>
      </div>
      {hasOp && result != null && <span style={{ font: "var(--type-mono-amount)", color: "var(--text-secondary)" }}>= {formatMoney(result, currency)}</span>}
      {error && <span role="alert" style={{ font: "var(--type-body-small)", fontWeight: 500 }}>{error}</span>}
    </div>
  );
}

/** Evaluates "45000+20000×2" with × ÷ precedence; returns integer VND. */
export function evalExpr(expr) {
  const toks = expr.match(/\d+|[+−×÷]/g) || [];
  const nums = [], ops = [];
  const prec = (o) => (o === "×" || o === "÷" ? 2 : 1);
  const apply = () => { const b = nums.pop(), a = nums.pop(), o = ops.pop(); nums.push(o === "+" ? a + b : o === "−" ? a - b : o === "×" ? a * b : b ? a / b : 0); };
  toks.forEach((t, i) => {
    if (/\d/.test(t)) nums.push(+t);
    else if (i === toks.length - 1) return;
    else { while (ops.length && prec(ops[ops.length - 1]) >= prec(t)) apply(); ops.push(t); }
  });
  while (ops.length && nums.length > 1) apply();
  return Math.round(nums[0] || 0);
}
