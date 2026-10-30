Manual amount readout (display-l pixel) with running calculator result. Drive with Keypad + applyKey.

```jsx
const [e,setE]=useState("");
<AmountField expression={e} />
<Keypad onKey={k => setE(applyKey(e,k))} />
```
