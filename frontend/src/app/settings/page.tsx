"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api, UserResponse, SubscriptionResponse } from "@/lib/api";
import {
  ArrowLeft,
  User,
  CreditCard,
  Shield,
  Loader2,
  Check,
  ExternalLink,
} from "lucide-react";

export default function SettingsPage() {
  const router = useRouter();
  const search_params = useSearchParams();

  const [user, set_user] = useState<UserResponse | null>(null);
  const [subscription, set_subscription] = useState<SubscriptionResponse | null>(null);
  const [loading, set_loading] = useState(true);
  const [active_tab, set_active_tab] = useState<"account" | "billing" | "security">("account");

  // Payment status from URL
  const payment_status = search_params.get("payment");

  useEffect(() => {
    load_data();
  }, []);

  const load_data = async () => {
    try {
      const [user_data, sub_data] = await Promise.all([
        api.get_me(),
        api.get_subscription().catch(() => ({ status: "none", plan: null, current_period_end: null, cancel_at_period_end: false })),
      ]);
      set_user(user_data);
      set_subscription(sub_data);
    } catch (err: any) {
      console.error("Failed to load settings:", err);
      if (err.status === 401) {
        router.push("/login");
      }
    } finally {
      set_loading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b sticky top-0 z-10">
        <div className="container mx-auto px-4 h-16 flex items-center gap-4">
          <Link
            href="/dashboard"
            className="text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <h1 className="font-bold text-lg">Settings</h1>
        </div>
      </header>

      {/* Payment Status Banner */}
      {payment_status === "success" && (
        <div className="bg-green-500/10 border-b border-green-500/20 px-4 py-3 text-sm text-green-600 flex items-center gap-2">
          <Check className="h-4 w-4" />
          Payment successful! Your subscription is now active.
        </div>
      )}
      {payment_status === "cancelled" && (
        <div className="bg-yellow-500/10 border-b border-yellow-500/20 px-4 py-3 text-sm text-yellow-600">
          Payment was cancelled. You can try again anytime.
        </div>
      )}

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Tab Navigation */}
          <div className="flex gap-1 border-b mb-8">
            {[
              { id: "account" as const, label: "Account", icon: User },
              { id: "billing" as const, label: "Billing", icon: CreditCard },
              { id: "security" as const, label: "Security", icon: Shield },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => set_active_tab(id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors ${
                  active_tab === id
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {active_tab === "account" && user && (
            <AccountTab user={user} on_update={load_data} />
          )}
          {active_tab === "billing" && (
            <BillingTab subscription={subscription} />
          )}
          {active_tab === "security" && <SecurityTab />}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// Account Tab
// ============================================================

function AccountTab({
  user,
  on_update,
}: {
  user: UserResponse;
  on_update: () => void;
}) {
  return (
    <div className="space-y-6">
      {/* Profile Info */}
      <div className="bg-card rounded-lg border p-6">
        <h2 className="font-medium mb-4">Profile Information</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-muted-foreground mb-1">
              Email
            </label>
            <input
              type="email"
              value={user.email}
              disabled
              className="w-full max-w-md px-3 py-2 border rounded-md bg-muted text-muted-foreground"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Email cannot be changed
            </p>
          </div>
          <div>
            <label className="block text-sm text-muted-foreground mb-1">
              Account Status
            </label>
            <div className="flex items-center gap-2">
              <span
                className={`px-2 py-1 rounded text-xs font-medium ${
                  user.is_active
                    ? "bg-green-100 text-green-700"
                    : "bg-red-100 text-red-700"
                }`}
              >
                {user.is_active ? "Active" : "Inactive"}
              </span>
            </div>
          </div>
          <div>
            <label className="block text-sm text-muted-foreground mb-1">
              Member Since
            </label>
            <p className="text-sm">
              {new Date(user.created_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-card rounded-lg border border-destructive/20 p-6">
        <h2 className="font-medium text-destructive mb-4">Danger Zone</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Once you delete your account, there is no going back. Please be
          certain.
        </p>
        <button className="px-4 py-2 border border-destructive text-destructive rounded-md hover:bg-destructive hover:text-destructive-foreground transition-colors text-sm">
          Delete Account
        </button>
      </div>
    </div>
  );
}

// ============================================================
// Billing Tab
// ============================================================

function BillingTab({
  subscription,
}: {
  subscription: SubscriptionResponse | null;
}) {
  const [loading, set_loading] = useState(false);

  const handle_manage = async () => {
    set_loading(true);
    try {
      const { portal_url } = await api.create_portal();
      window.location.href = portal_url;
    } catch (err: any) {
      console.error("Failed to open portal:", err);
      alert(err.detail || "Failed to open billing portal");
    } finally {
      set_loading(false);
    }
  };

  const handle_subscribe = async (price_id: string) => {
    set_loading(true);
    try {
      const { checkout_url } = await api.create_checkout(price_id);
      window.location.href = checkout_url;
    } catch (err: any) {
      console.error("Failed to create checkout:", err);
      alert(err.detail || "Failed to start checkout");
    } finally {
      set_loading(false);
    }
  };

  const is_active = subscription?.status === "active";

  return (
    <div className="space-y-6">
      {/* Current Plan */}
      <div className="bg-card rounded-lg border p-6">
        <h2 className="font-medium mb-4">Current Plan</h2>
        {is_active ? (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm font-medium">
                Pro Plan
              </span>
              {subscription.cancel_at_period_end && (
                <span className="text-sm text-yellow-600">
                  Cancels at period end
                </span>
              )}
            </div>
            {subscription.current_period_end && (
              <p className="text-sm text-muted-foreground">
                Current period ends:{" "}
                {new Date(
                  parseInt(subscription.current_period_end) * 1000
                ).toLocaleDateString()}
              </p>
            )}
            <button
              onClick={handle_manage}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-secondary text-sm disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ExternalLink className="h-4 w-4" />
              )}
              Manage Subscription
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-muted-foreground">
              You are on the free plan. Upgrade to unlock all features.
            </p>
            <div className="text-sm text-muted-foreground">
              <span className="text-foreground font-medium">Free plan includes:</span>
              <ul className="mt-2 space-y-1">
                <li>- 3 projects</li>
                <li>- Basic LBO analysis</li>
                <li>- Excel export</li>
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Pricing */}
      {!is_active && (
        <div className="bg-card rounded-lg border p-6">
          <h2 className="font-medium mb-4">Upgrade to Pro</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {/* Monthly */}
            <div className="border rounded-lg p-4 hover:border-primary transition-colors">
              <h3 className="font-medium">Monthly</h3>
              <div className="mt-2">
                <span className="text-3xl font-bold">$29</span>
                <span className="text-muted-foreground">/month</span>
              </div>
              <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
                <li>- Unlimited projects</li>
                <li>- AI chat assistant</li>
                <li>- Document extraction</li>
                <li>- Advanced analysis</li>
                <li>- Priority support</li>
              </ul>
              <button
                onClick={() => handle_subscribe("price_monthly")}
                disabled={loading}
                className="w-full mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 text-sm disabled:opacity-50"
              >
                {loading ? "Loading..." : "Subscribe Monthly"}
              </button>
            </div>

            {/* Annual */}
            <div className="border-2 border-primary rounded-lg p-4 relative">
              <span className="absolute -top-3 left-4 bg-primary text-primary-foreground text-xs px-2 py-1 rounded">
                Save 20%
              </span>
              <h3 className="font-medium">Annual</h3>
              <div className="mt-2">
                <span className="text-3xl font-bold">$279</span>
                <span className="text-muted-foreground">/year</span>
              </div>
              <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
                <li>- Unlimited projects</li>
                <li>- AI chat assistant</li>
                <li>- Document extraction</li>
                <li>- Advanced analysis</li>
                <li>- Priority support</li>
              </ul>
              <button
                onClick={() => handle_subscribe("price_annual")}
                disabled={loading}
                className="w-full mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 text-sm disabled:opacity-50"
              >
                {loading ? "Loading..." : "Subscribe Annually"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// Security Tab
// ============================================================

function SecurityTab() {
  const [current_password, set_current_password] = useState("");
  const [new_password, set_new_password] = useState("");
  const [confirm_password, set_confirm_password] = useState("");
  const [loading, set_loading] = useState(false);
  const [message, set_message] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const handle_change_password = async (e: React.FormEvent) => {
    e.preventDefault();

    if (new_password !== confirm_password) {
      set_message({ type: "error", text: "Passwords do not match" });
      return;
    }

    if (new_password.length < 8) {
      set_message({
        type: "error",
        text: "Password must be at least 8 characters",
      });
      return;
    }

    set_loading(true);
    set_message(null);

    // Note: Password change endpoint would need to be added to the backend
    // For now, show a placeholder message
    setTimeout(() => {
      set_loading(false);
      set_message({
        type: "success",
        text: "Password change feature coming soon",
      });
      set_current_password("");
      set_new_password("");
      set_confirm_password("");
    }, 1000);
  };

  return (
    <div className="space-y-6">
      {/* Change Password */}
      <div className="bg-card rounded-lg border p-6">
        <h2 className="font-medium mb-4">Change Password</h2>
        <form onSubmit={handle_change_password} className="space-y-4 max-w-md">
          {message && (
            <div
              className={`p-3 rounded text-sm ${
                message.type === "success"
                  ? "bg-green-100 text-green-700"
                  : "bg-red-100 text-red-700"
              }`}
            >
              {message.text}
            </div>
          )}
          <div>
            <label className="block text-sm text-muted-foreground mb-1">
              Current Password
            </label>
            <input
              type="password"
              value={current_password}
              onChange={(e) => set_current_password(e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-background"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-muted-foreground mb-1">
              New Password
            </label>
            <input
              type="password"
              value={new_password}
              onChange={(e) => set_new_password(e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-background"
              required
              minLength={8}
            />
          </div>
          <div>
            <label className="block text-sm text-muted-foreground mb-1">
              Confirm New Password
            </label>
            <input
              type="password"
              value={confirm_password}
              onChange={(e) => set_confirm_password(e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-background"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 text-sm disabled:opacity-50"
          >
            {loading ? "Updating..." : "Update Password"}
          </button>
        </form>
      </div>

      {/* Session Info */}
      <div className="bg-card rounded-lg border p-6">
        <h2 className="font-medium mb-4">Session</h2>
        <p className="text-sm text-muted-foreground mb-4">
          You can log out from all devices by clicking the button below.
        </p>
        <button className="px-4 py-2 border rounded-md hover:bg-secondary text-sm">
          Log Out All Devices
        </button>
      </div>
    </div>
  );
}
