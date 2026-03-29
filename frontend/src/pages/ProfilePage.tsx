import { useAuth } from "@/contexts/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { User, Mail, Briefcase, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8 max-w-lg">
        <div className="mb-8 animate-fade-in">
          <h1 className="text-3xl font-heading text-foreground">Profile</h1>
          <p className="text-muted-foreground mt-1">Your account details</p>
        </div>

        <Card className="card-surface animate-fade-in">
          <CardHeader className="text-center">
            <div className="mx-auto w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mb-2">
              <User className="h-10 w-10 text-primary" />
            </div>
            <CardTitle className="font-heading text-xl">{user?.name}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3 p-3 rounded-lg bg-accent/30">
              <Mail className="h-5 w-5 text-secondary" />
              <div>
                <p className="text-xs text-muted-foreground">Email</p>
                <p className="text-sm font-medium">{user?.email}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg bg-accent/30">
              <Briefcase className="h-5 w-5 text-secondary" />
              <div>
                <p className="text-xs text-muted-foreground">Role</p>
                <p className="text-sm font-medium">{user?.role}</p>
              </div>
            </div>
            <Button variant="outline" className="w-full mt-4 text-destructive border-destructive/30 hover:bg-destructive/10" onClick={handleLogout}>
              <LogOut className="h-4 w-4 mr-2" />
              Sign Out
            </Button>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
