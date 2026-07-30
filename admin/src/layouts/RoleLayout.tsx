import { ReactNode, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { LogOut } from "lucide-react";
import { session } from "../services/api";
import { adminLanguage, setAdminLanguage, tr } from "../services/i18n";

export type NavItem = { to: string; label: string; icon: ReactNode };
function RoleLayout({
  title,
  subtitle,
  items,
}: {
  title: string;
  subtitle: string;
  items: NavItem[];
}) {
  const [language, setLanguage] = useState(adminLanguage());
  function switchLanguage() {
    const next = language === "az" ? "en" : "az";
    setAdminLanguage(next);
    setLanguage(next);
  }
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">MARTIQ</div>
        <div className="role-title">{tr(title)}</div>
        <div className="group">{subtitle}</div>
        {items.map((item) => (
          <NavLink
            end={item.to.split("/").length <= 3}
            className="nav"
            key={item.to}
            to={item.to}
          >
            {item.icon}
            <span>{tr(item.label)}</span>
          </NavLink>
        ))}
        <button className="nav" aria-label={tr("Dil")} onClick={switchLanguage}>
          <span>{language === "az" ? "EN" : "AZ"}</span>
        </button>
        <button
          className="nav logout"
          onClick={() => {
            session.logout();
            location.href = "/";
          }}
        >
          <LogOut />
          <span>{tr("Çıxış")}</span>
        </button>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
export const BranchLayout = ({ items }: { items: NavItem[] }) => (
  <RoleLayout
    title="Filial idarəetməsi"
    subtitle="BRANCH ADMIN"
    items={items}
  />
);
export const HeadLayout = ({ items }: { items: NavItem[] }) => (
  <RoleLayout title="Şəbəkə idarəetməsi" subtitle="HEAD OFFICE" items={items} />
);
export const PlatformLayout = ({ items }: { items: NavItem[] }) => (
  <RoleLayout
    title="Platform idarəetməsi"
    subtitle="PLATFORM ADMIN"
    items={items}
  />
);
