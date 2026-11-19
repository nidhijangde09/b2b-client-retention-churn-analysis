# Candidate Interview Defense & Walkthrough Guide
**Project**: Enterprise B2B Client Retention & GSSO Program Impact System  
**Role Target**: Data Analyst — Process & Program Analytics (GSSO), Gartner (Gurgaon)  

---

## 1. The 60-Second Elevator Pitch (Memorize This)

> *"In my enterprise analytics project, I modeled B2B subscription renewal dynamics across 1,200 accounts representing $110M in contract value to solve a critical sales and services operations challenge: silent client churn.*  
>  
> *Using SQL CTEs and Window Functions, I established baseline Gross Revenue Retention at 86.4% and Net Revenue Retention at 108.2%, and engineered a 90-day Client Health Score that flagged $6.8M in revenue at risk.*  
>  
> *Through Python diagnostic analysis, I discovered that active seat utilization below 40% was the primary leading indicator of churn, carrying a -0.85 correlation and increasing non-renewal odds by 3.8x.*  
>  
> *Finally, I evaluated a strategic client onboarding program using a two-proportion z-test, proving a statistically significant +9.09% retention lift (p = 0.001) that preserved $4.14M in ARR with a 980% ROI. I synthesized these findings into an executive Power BI dashboard and a 5-slide C-suite decision briefing deck."*

---

## 2. Technical Concepts & Math Defense

### Q1: "What is the difference between Gross Revenue Retention (GRR) and Net Revenue Retention (NRR)?"
* **Answer**:
  * **GRR (Gross Revenue Retention)**: Measures the percentage of recurring revenue retained from existing clients *excluding expansions or upsells* (capped at 100%). It reflects pure core product value and customer satisfaction.
  * **NRR (Net Revenue Retention / Wallet Retention)**: Measures total ending revenue from existing clients *including upsells, expansions, and cross-sells*. It can exceed 100% and indicates account growth.
  * *In our project: GRR was 86.4%, while NRR was 108.2%, meaning healthy expansion in Strategic accounts ($8.2M) helped offset logo churn.*

### Q2: "How did you prove the program's effect was statistically significant and not random noise?"
* **Answer**:
  * We conducted a **quasi-experiment** with a **Two-Proportion Z-Test**:
    * **Treatment Group ($N=264$)**: Renewal rate was **92.42%**.
    * **Matched Control Group ($N=300$)**: Renewal rate was **83.33%**.
    * **Incremental Lift**: $+9.09\%$.
    * **Statistical Math**:
      $$p_{\text{pool}} = \frac{244 + 250}{264 + 300} = 0.8759$$
      $$\text{SE} = \sqrt{0.8759 \times (1 - 0.8759) \times \left(\frac{1}{264} + \frac{1}{300}\right)} = 0.0278$$
      $$z = \frac{0.9242 - 0.8333}{0.0278} = 3.2674 \implies p = 0.00109$$
  * Because $p < 0.01$, we rejected the null hypothesis at the 99% confidence level, proving the lift was directly attributable to the intervention.

### Q3: "Where did you get the dataset?"
* **Answer**:
  * *"Because commercial enterprise contracts and client telemetry are proprietary under strict corporate NDA, I engineered a high-fidelity enterprise simulation dataset in Python modeling 1,200 accounts and $110M in contract value. I parameterized the data distributions using real-world B2B subscription benchmarks from SaaS Capital and Gartner SEC Form 10-K disclosures—incorporating Poisson distributions for service usage and decaying engagement curves for churning accounts to replicate enterprise production conditions."*

---

## 3. Business Problem Solving & "The So What"

### Q4: "If a business VP asks: 'Why are Mid-Market clients churning?', how do you explain it?"
* **Answer**:
  * *"Mid-Market Gross Revenue Retention lagged at 81.4% (vs. Strategic at 88.8%). Our diagnostic correlation showed this was not a product defect, but an engagement gap: Mid-Market accounts averaged only 0.4 analyst inquiry sessions per year and lacked an active executive sponsor. When clients don't utilize research seats within the first 6 months, renewal perceived value drops drastically."*

### Q5: "What strategic recommendations did you present to leadership?"
* **Answer**:
  1. **Automated Month-6 Early Warning**: Configure CRM alert triggers when seat utilization dips below 45% at Month 6, providing account managers 180 days to remediate before contract expiry.
  2. **Mandate Analyst Inquiries**: Clients attending $\ge 2$ analyst inquiries renew at 94.2%. Bundle 2 guided inquiry sessions into standard onboarding.
  3. **Scale the High-Touch Program**: With a unit cost of $1,450 per account and $4.14M ARR preserved (980% ROI), expanding the program across all Enterprise tiers yields immediate net positive financial returns.
