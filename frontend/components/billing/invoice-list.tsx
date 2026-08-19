import { FileText } from "lucide-react";

import type { BillingInvoice } from "@/lib/types";
import { formatDate, formatMoney } from "./format";

export function InvoiceList({ invoices }: { invoices: BillingInvoice[] }) {
  return <section className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="font-black">Invoices</h2><p className="mt-1 text-xs text-slate-500">Receipts created after verified payments.</p><div className="mt-4 space-y-2">{invoices.map((invoice) => <article key={invoice.id} className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-100 p-3"><span className="grid size-9 place-items-center rounded-lg bg-indigo-50 text-indigo-600"><FileText size={16} /></span><div className="min-w-36 flex-1"><p className="text-xs font-black">{invoice.invoice_number}</p><p className="text-[10px] text-slate-500">{invoice.plan_name} · {formatDate(invoice.issued_at)}</p></div><strong className="text-xs">{formatMoney(invoice.amount_minor, invoice.currency)}</strong><span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-bold capitalize text-slate-600">{invoice.status}</span></article>)}{!invoices.length && <p className="py-8 text-center text-xs text-slate-400">No invoices yet.</p>}</div></section>;
}
