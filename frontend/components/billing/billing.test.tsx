import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { BillingPlan, BillingSubscription } from "@/lib/types";
import { CheckoutModal } from "./checkout-modal";
import { PricingCard } from "./pricing-card";
import { SubscriptionStatus } from "./subscription-status";

const plan: BillingPlan = {
  id: "plan-1", code: "pro", name: "Pro", description: "Advanced learning",
  amount_minor: 100, compare_at_amount_minor: 99900, currency: "INR", billing_interval: "month", duration_days: 30,
  features: ["AI tutor", "Unlimited projects"], limits: { coding_projects: null }, is_featured: true,
};

describe("billing components", () => {
  it("renders the server plan price and starts selection", () => {
    const select = vi.fn();
    render(<PricingCard plan={plan} current={false} onSelect={select} />);
    expect(screen.getByText("₹999")).toHaveClass("line-through");
    expect(screen.getByText("₹1")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Upgrade" }));
    expect(select).toHaveBeenCalledWith(plan);
  });

  it("explains that Checkout is handled by Razorpay", () => {
    render(<CheckoutModal plan={plan} busy={false} onClose={vi.fn()} onConfirm={vi.fn()} />);
    expect(screen.getByText(/collected directly by Razorpay/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /secure payment/i })).toBeEnabled();
  });

  it("shows cancellation-at-period-end state", () => {
    const subscription: BillingSubscription = {
      id: "sub-1", plan, provider: "razorpay", status: "active", started_at: "2026-01-01T00:00:00Z",
      current_period_start: "2026-01-01T00:00:00Z", current_period_end: "2026-02-01T00:00:00Z",
      cancel_at_period_end: true, cancelled_at: "2026-01-15T00:00:00Z", ended_at: null,
    };
    render(<SubscriptionStatus subscription={subscription} onCancel={vi.fn()} cancelling={false} />);
    expect(screen.getByText(/cancels at the end/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /cancel at period/i })).not.toBeInTheDocument();
  });
});
