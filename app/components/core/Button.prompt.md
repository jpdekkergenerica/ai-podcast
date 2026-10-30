Primary text actions. One primary per screen; pair destructive only with a secondary "Huỷ".

```jsx
<Button>Lưu</Button>
<Button variant="secondary" icon="edit">Sửa</Button>
<Button variant="tertiary">Bỏ qua</Button>
<Button variant="destructive">Xoá ví</Button>
<Button loading fullWidth>Lưu</Button>
```

- Pressed: primary steps to gray-700; secondary inverts; tertiary gets a gray-100 wash.
- Focus: 2px outline, 2px offset. Disabled: gray-100 fill, gray-400 text.
- Labels are verbs in sentence case ("Lưu giao dịch"), never "OK".
