import React, { useState } from "react";
import { BottomSheet } from "./BottomSheet.jsx";
import { Button } from "../core/Button.jsx";
import { Icon } from "../core/Icon.jsx";

function Check({ checked, onChange, children, required }) {
  return (
    <label style={{ display: "flex", gap: 12, alignItems: "flex-start", padding: "12px 0", borderTop: "var(--border-1) solid var(--border-default)", cursor: "pointer" }}>
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} style={{ position: "absolute", opacity: 0, width: 1, height: 1 }} />
      <span style={{ width: 24, height: 24, flex: "none", boxSizing: "border-box", border: "var(--border-2) solid var(--border-strong)", background: checked ? "var(--bg-inverse)" : "transparent", color: "var(--text-inverse)", display: "inline-flex", alignItems: "center", justifyContent: "center" }}>
        {checked && <span style={{ display: "inline-flex", margin: -2 }}><Icon name="check" /></span>}
      </span>
      <span style={{ font: "var(--type-body-small)", color: "var(--text-primary)", textWrap: "pretty" }}>{children}{required && <span style={{ color: "var(--text-secondary)" }}> (bắt buộc)</span>}</span>
    </label>
  );
}

/** Permission & consent for AI processing of text, voice and images. */
export function ConsentSheet({ open = true, onAccept, onDecline, inline, kind = "ai" }) {
  const [a, setA] = useState(true);
  const [b, setB] = useState(false);
  const copy = {
    ai: { icon: "lock", title: "Cho phép AI xử lý dữ liệu chi tiêu", body: "Monsey dùng AI để hiểu tin nhắn, giọng nói và ảnh hoá đơn bạn gửi, rồi tạo giao dịch. Bạn luôn xem lại trước khi lưu." },
    mic: { icon: "mic", title: "Cho phép dùng micro", body: "Để ghi chi tiêu bằng giọng nói. Âm thanh chỉ được xử lý khi bạn giữ nút micro." },
    camera: { icon: "camera", title: "Cho phép dùng camera", body: "Để chụp hoá đơn hoặc ảnh chuyển khoản. Ảnh được lưu kèm giao dịch trong máy bạn." },
  }[kind];
  return (
    <BottomSheet open={open} inline={inline} onClose={onDecline}
      footer={<><Button fullWidth disabled={kind === "ai" && !a} onClick={() => onAccept && onAccept({ processing: a, improve: b })}>Đồng ý</Button><Button fullWidth variant="tertiary" onClick={onDecline}>Để sau</Button></>}>
      <div style={{ display: "flex", flexDirection: "column", gap: 12, paddingTop: 8 }}>
        <Icon name={copy.icon} filled />
        <span style={{ font: "var(--type-title)", letterSpacing: "var(--ls-title)", textWrap: "pretty" }}>{copy.title}</span>
        <span style={{ font: "var(--type-body)", color: "var(--text-secondary)", textWrap: "pretty" }}>{copy.body}</span>
        {kind === "ai" && <div>
          <Check checked={a} onChange={setA} required>Xử lý nội dung tôi gửi để tạo giao dịch. Dữ liệu được mã hoá và không bán cho bên thứ ba.</Check>
          <Check checked={b} onChange={setB}>Dùng dữ liệu đã ẩn danh để cải thiện độ chính xác của AI.</Check>
          <a href="#" style={{ font: "var(--type-label)", display: "inline-block", padding: "8px 0" }}>Chính sách quyền riêng tư</a>
        </div>}
      </div>
    </BottomSheet>
  );
}
