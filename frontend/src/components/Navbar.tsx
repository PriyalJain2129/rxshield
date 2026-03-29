import { Link, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { ShieldCheck, LayoutDashboard, Users, ClipboardList, User, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/patients", label: "Patients", icon: Users },
  { to: "/orders", label: "Orders & Alerts", icon: ClipboardList },
  { to: "/profile", label: "Profile", icon: User },
];

export default function Navbar() {
  const { logout } = useAuth();
  const location = useLocation();

  return (
    <nav className="bg-primary text-primary-foreground shadow-lg">
      <div className="container mx-auto flex items-center justify-between h-16 px-4">
        <Link to="/dashboard" className="flex items-center gap-2 font-heading text-xl tracking-wide">
          <ShieldCheck className="h-7 w-7 text-accent" />
          RxShield
        </Link>
        <div className="hidden md:flex items-center gap-1">
          {navItems.map((item) => {
            const active = location.pathname === item.to;
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  active ? "bg-secondary text-secondary-foreground" : "hover:bg-primary-foreground/10"
                }`}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
          <Button
            variant="ghost"
            size="sm"
            onClick={logout}
            className="ml-2 text-primary-foreground hover:bg-primary-foreground/10"
          >
            <LogOut className="h-4 w-4 mr-1" />
            Logout
          </Button>
        </div>
      </div>
    </nav>
  );
}
