Calculator keypad; reduce input with applyKey().

```jsx
<Keypad onKey={k => k === "done" ? save() : setE(applyKey(e, k))} />
```
