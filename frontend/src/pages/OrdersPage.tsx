import { useQuery } from "@tanstack/react-query";
import { getOrders, getAlerts } from "@/lib/api";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Navbar from "@/components/Navbar";

export default function OrdersPage() {
  const { data: orders = [] } = useQuery({ queryKey: ["orders"], queryFn: getOrders });
  const { data: alerts = [] } = useQuery({ queryKey: ["alerts"], queryFn: getAlerts });

  const statusBadge = (status: string) => {
    switch (status?.toUpperCase?.() ?? status) {
      case "APPROVED":
        return <Badge className="bg-emerald-600 hover:bg-emerald-600 text-white">Approved</Badge>;
      case "FLAGGED":
        return <Badge variant="destructive">Flagged</Badge>;
      case "safe":
        return <Badge className="bg-success text-success-foreground">Safe</Badge>;
      case "warning":
        return <Badge className="bg-warning text-warning-foreground">Warning</Badge>;
      case "danger":
        return <Badge variant="destructive">Danger</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <div className="mb-6 animate-fade-in">
          <h1 className="text-3xl font-heading text-foreground">Orders & Alerts</h1>
          <p className="text-muted-foreground mt-1">Review prescription history and safety flags</p>
        </div>

        <Tabs defaultValue="orders" className="animate-fade-in">
          <TabsList className="mb-4">
            <TabsTrigger value="orders">Prescriptions ({orders.length})</TabsTrigger>
            <TabsTrigger value="alerts">Safety Alerts ({alerts.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="orders">
            <div className="card-surface overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-primary/5">
                    <TableHead>Order ID</TableHead>
                    <TableHead>Patient</TableHead>
                    <TableHead>Drug</TableHead>
                    <TableHead>Dose (mg)</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {orders.map((o) => (
                    <TableRow key={o.id} className="hover:bg-accent/30 transition-colors">
                      <TableCell className="font-mono text-sm">{o.id}</TableCell>
                      <TableCell className="font-medium">{o.patient ?? o.patient_name ?? "—"}</TableCell>
                      <TableCell>{o.drug}</TableCell>
                      <TableCell>{o.dose}</TableCell>
                      <TableCell>{o.date}</TableCell>
                      <TableCell>{statusBadge(o.status)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>

          <TabsContent value="alerts">
            <div className="card-surface overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-primary/5">
                    <TableHead>Order ID</TableHead>
                    <TableHead>Patient</TableHead>
                    <TableHead>Drug</TableHead>
                    <TableHead>Dose (mg)</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {alerts.map((a) => (
                    <TableRow key={a.id} className="hover:bg-accent/30 transition-colors">
                      <TableCell className="font-mono text-sm">{a.id}</TableCell>
                      <TableCell className="font-medium">{a.patient ?? a.patient_name ?? "—"}</TableCell>
                      <TableCell>{a.drug}</TableCell>
                      <TableCell>{a.dose}</TableCell>
                      <TableCell>{a.date}</TableCell>
                      <TableCell>{statusBadge(a.status)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
