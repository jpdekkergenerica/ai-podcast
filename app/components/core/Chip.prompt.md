Filter / choice chips and the currency-code chip.

```jsx
<Chip selected>Tháng này</Chip>
<Chip icon="coffee" onRemove={() => {}}>Ăn uống</Chip>
<Chip variant="code">USD</Chip>
```

- Uses radius-sm (4px) — the single rounded exception, marking "tappable & dismissible" vs sharp data cells.
- Show the code chip whenever a wallet/amount is not in the default currency (VND).
