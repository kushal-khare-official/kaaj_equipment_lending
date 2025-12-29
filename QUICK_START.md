# Quick Start Guide - New Features

## 🚀 Getting Started

### 1. Update Database with New Lenders

```bash
cd backend
python -m scripts.seed_lenders
```

This will create 5 lenders with different term/rate configurations.

---

## 📋 Feature Overview

### Feature 1: Smart Document Requests
Documents are now automatically requested based on verification check results.

### Feature 2: Test Data for All Scenarios
Use specific SSN/business name patterns to trigger different scenarios.

### Feature 3: Loan Terms & Rates
Each lender offers different terms and rates based on equipment and credit quality.

### Feature 4: Login Protection
Underwriter pages require login (use any username/password in demo mode).

---

## 🧪 Quick Test Scenarios

### Scenario A: Perfect Application
```
Business Name: EXCELLENT TRUCKING INC
Guarantor SSN: 111-11-1111
Expected: All checks pass, 5 eligible lenders, best terms displayed
```

### Scenario B: Needs Manual Review
```
Business Name: FAIR LOGISTICS LLC  
Guarantor SSN: 333-33-3333 (address mismatch)
Expected: KYC needs review, documents requested, manual review required
```

### Scenario C: High Risk
```
Business Name: POOR TRANSPORT CO
Guarantor SSN: 555-55-5555 (watchlist hit)
Bank Statement URL: nsf_statement.pdf
Expected: Multiple red flags, extensive documents requested
```

### Scenario D: Startup
```
Business Name: NEW STARTUP DELIVERY
Guarantor SSN: 222-22-2222 (good credit)
Expected: No business credit, relies on personal credit, startup-friendly lenders match
```

---

## 🔐 Using Protected Pages

1. Navigate to `http://localhost:5173/uw`
2. You'll be redirected to `/login`
3. Enter any username and password (e.g., `admin` / `password`)
4. You'll be redirected back to the underwriter page
5. Your username appears in the header with a Logout button

To logout: Click "Logout" in the header or navigate to any protected page after clearing localStorage.

---

## 📊 Viewing Loan Terms

When viewing an application in Documents or Review step:
1. Look for the "Best Available Terms" badge
2. This shows the highest term (longest loan) and lowest rate among ALL eligible lenders
3. Individual lender cards show their specific term and rate offers

Example:
```
Best Available Terms: 84 months • 5.99% APR
```

This means across all matched lenders:
- One lender offers up to 84 months
- One lender offers as low as 5.99% interest rate
- (These may be from different lenders)

---

## 📄 Understanding Document Requests

### Automatic Document Requests
The system automatically requests documents when:
- Credit check fails or shows concerning factors
- KYC/KYB verification fails
- Bank statements show NSF fees or overdrafts
- Risk level is HIGH or CRITICAL

### Document Categories
- **Identity**: Driver's license, passport, SSN card
- **Business**: Articles of incorporation, business license, EIN letter
- **Financial**: Tax returns, P&L statements, bank statements
- **Banking**: Voided checks, bank letters
- **Equipment**: Invoices, bills of sale
- **Supporting**: Explanation letters, references

### Example Flow
1. Application has FICO 620 (poor credit)
2. System automatically requests:
   - Personal financial statement
   - Explanation letter
   - Additional bank statements
3. User sees these in Step 4 with descriptions explaining why

---

## 🎯 Test Data Quick Reference

### Credit Scores (SSN)
| SSN | FICO | Result |
|-----|------|--------|
| 111-11-1111 | 785 | ✅ Excellent |
| 222-22-2222 | 725 | ✅ Good |
| 333-33-3333 | 670 | ⚠️ Fair |
| 444-44-4444 | 620 | ❌ Poor |
| 555-55-5555 | 540 | ❌ Bad |

### Business Credit (Business Name)
| Name Contains | PayNet | Result |
|--------------|--------|--------|
| EXCELLENT | 865 | ✅ Excellent |
| GOOD | 775 | ✅ Good |
| FAIR | 670 | ⚠️ Fair |
| POOR | 580 | ❌ Poor |
| STARTUP | N/A | ⚠️ No history |

### Bank Statements (Document URL)
| URL Contains | Grade | Result |
|-------------|-------|--------|
| excellent | A+ | ✅ Strong |
| good | A | ✅ Good |
| fair | B | ⚠️ Acceptable |
| poor | C | ⚠️ Weak |
| nsf | D | ❌ High risk |

---

## 🎨 Visual Indicators

### Document Status
- 🟢 Green border + checkmark = Uploaded
- 🟡 Amber border + warning = Required by workflow
- ⚪ Gray border + document icon = Optional/standard

### Lender Match Status
- 🟢 Green badge = Eligible
- 🔴 Red badge = Not Eligible
- 🔵 Blue badge = Best Available Terms

### Review Status
- 🟢 Auto-Approved = All checks passed
- 🟡 Pending Manual Review = Some checks need attention
- ⚪ Pending = Awaiting workflow completion
- 🔴 Rejected = Application declined

---

## 💡 Tips

1. **Testing Workflows**: Use the test SSNs and business names to trigger specific scenarios
2. **Best Terms**: Multiple eligible lenders show which offers the best overall package
3. **Documents**: Pay attention to workflow-requested documents (amber) vs standard (gray)
4. **Login**: Any credentials work in demo mode - it's just for UI demonstration

---

## 🐛 Troubleshooting

### No lenders showing as eligible
- Check that you ran `seed_lenders.py` to load lender data
- Verify FICO and PayNet scores meet lender criteria
- Check loan amount is within lender min/max

### Documents not showing in Step 4
- Ensure you've progressed through all previous steps
- Documents are only requested after checks run
- Check that workflow completed (look for status indicator)

### Protected pages not working
- Clear localStorage and login again
- Check browser console for errors
- Ensure you're accessing `/uw` or `/applications` routes

---

## 📚 Additional Resources

- See `README.md` for complete test data tables
- See `CHANGELOG.md` for detailed implementation notes
- See `DESIGN.md` for system architecture
- See API docs at `http://localhost:8000/docs`

