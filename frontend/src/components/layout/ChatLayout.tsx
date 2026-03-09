import { useState, useCallback, useMemo } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { ChatSidebar, type PanelName } from "./ChatSidebar";
import { ChatHeader } from "./ChatHeader";
import { useKeyboardShortcuts, useShortcutsDialog } from "@/hooks/useKeyboardShortcuts";
import { KeyboardShortcutsDialog } from "@/components/shared/KeyboardShortcutsDialog";
import { AppModal, type SectionId } from "@/components/shared/AppModal";

const SIDEBAR_KEY = "nullbook-sidebar-collapsed";

function getInitialCollapsed(): boolean {
  const stored = localStorage.getItem(SIDEBAR_KEY);
  if (stored !== null) return stored === "true";
  return false;
}

const SETTINGS_SECTIONS = new Set<string>(["settings"]);

export function ChatLayout() {
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(getInitialCollapsed);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [section, setSection] = useState<SectionId>("accounts");
  const shortcutsDialog = useShortcutsDialog();

  const toggleCollapsed = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem(SIDEBAR_KEY, String(next));
      return next;
    });
  }, []);

  // Derive activePanel for sidebar highlighting
  const activePanel: PanelName = modalOpen
    ? SETTINGS_SECTIONS.has(section)
      ? "settings"
      : (section as PanelName)
    : null;

  const handlePanelChange = useCallback((panel: PanelName) => {
    if (panel) {
      const newSection: SectionId = panel === "settings" ? "settings" : (panel as SectionId);
      setSection(newSection);
      setModalOpen(true);
    } else {
      setModalOpen(false);
    }
  }, []);

  const handleSectionChange = useCallback((newSection: SectionId) => {
    setSection(newSection);
  }, []);

  const shortcuts = useMemo(
    () => [
      {
        key: "k",
        meta: true,
        description: "Focus chat input",
        action: () => {
          const input = document.querySelector<HTMLTextAreaElement>("[data-chat-input]");
          input?.focus();
        },
      },
      {
        key: "n",
        meta: true,
        description: "New conversation",
        action: () => navigate("/"),
      },
      {
        key: "Escape",
        description: "Close modal",
        action: () => setModalOpen(false),
      },
      {
        key: "?",
        description: "Keyboard shortcuts",
        action: shortcutsDialog.toggle,
      },
    ],
    [navigate, shortcutsDialog.toggle]
  );

  useKeyboardShortcuts(shortcuts);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Desktop sidebar */}
      <div className="hidden md:flex">
        <ChatSidebar
          collapsed={collapsed}
          onToggle={toggleCollapsed}
          activePanel={activePanel}
          onPanelChange={handlePanelChange}
        />
      </div>

      {/* Mobile sidebar as sheet */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="w-72 p-0">
          <ChatSidebar
            collapsed={false}
            onToggle={() => setMobileOpen(false)}
            activePanel={activePanel}
            onPanelChange={(panel) => {
              handlePanelChange(panel);
              setMobileOpen(false);
            }}
          />
        </SheetContent>
      </Sheet>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <ChatHeader onMenuClick={() => setMobileOpen(true)} />
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>

      {/* Unified modal for all sections */}
      <AppModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        section={section}
        onSectionChange={handleSectionChange}
      />

      <KeyboardShortcutsDialog open={shortcutsDialog.open} onOpenChange={shortcutsDialog.setOpen} />
    </div>
  );
}
