import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { KnowledgeFolder } from "@/lib/types";
import { MarkdownPreview } from "./markdown-preview";
import { WorkspaceNav } from "./workspace-nav";

const folder: KnowledgeFolder = {
  id: "folder-1",
  parent_id: null,
  name: "Authentication",
  color: "#4F46E5",
  is_favorite: false,
  item_count: 3,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("knowledge base components", () => {
  it("renders Markdown headings and checklist state", () => {
    render(
      <MarkdownPreview
        content={"# JWT Authentication\n- [x] Review refresh tokens"}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "JWT Authentication" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("checkbox")).toBeChecked();
    expect(screen.getByText("Review refresh tokens")).toBeInTheDocument();
  });

  it("navigates to a user-owned folder", () => {
    const selectFolder = vi.fn();
    render(
      <WorkspaceNav
        view="overview"
        folders={[folder]}
        selectedFolder={null}
        onView={vi.fn()}
        onFolder={selectFolder}
        onNewFolder={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Authentication/ }));
    expect(selectFolder).toHaveBeenCalledWith("folder-1");
    expect(screen.getByText("3")).toBeInTheDocument();
  });
});
