Category grid or wallet list in a bottom sheet.

```jsx
<PickerSheet type="category" value="food" onSelect={setCat} onClose={close} />
<PickerSheet type="wallet" value="cash" wallets={[{id:"cash",name:"Tiền mặt",balance:1250000},{id:"usd",name:"Wise",currency:"USD",balance:320.4}]} />
```
