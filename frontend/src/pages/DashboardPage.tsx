import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getPatients, getDrugs, checkOrder, SafetyResult, createOrder } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ShieldCheck, ShieldAlert, AlertTriangle, CheckCircle2, Pill } from "lucide-react";
import { toast } from "sonner";
import Navbar from "@/components/Navbar";

export default function DashboardPage() {
  // Fetching real data from your Flask backend
  const { data: patients = [] } = useQuery({ queryKey: ["patients"], queryFn: getPatients });
  const { data: drugs = [] } = useQuery({ queryKey: ["drugs"], queryFn: getDrugs });

  const [patientId, setPatientId] = useState("");
  const [drugName, setDrugName] = useState(""); 
  const [dose, setDose] = useState("");
  const [results, setResults] = useState<SafetyResult[] | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [checking, setChecking] = useState(false);

  const handleCheck = async () => {
    if (!patientId || !drugName || !dose) {
      toast.error("Please fill all fields.");
      return;
    }
    setChecking(true);
    try {
      // Calling the safety engine in app.py
      const res = await checkOrder(patientId, drugName, parseFloat(dose));
      setResults(res);
      setModalOpen(true);
    } catch (error) {
      console.error("Safety check failed:", error);
      toast.error("Safety check failed. Is your Flask backend running?");
    } finally {
      setChecking(false);
    }
  };

  const handleSubmitOrder = async () => {
    try {
      // FIXED: Sending as a single object to match api.ts and backend request.get_json()
      await createOrder({ 
        patient_id: patientId, 
        drug_name: drugName, 
        dosage: parseFloat(dose) 
      });
      
      toast.success("Order submitted and saved to database.");
      setModalOpen(false);
      setPatientId("");
      setDrugName("");
      setDose("");
      setResults(null);
    } catch (error) {
      console.error("Submit failed:", error);
      toast.error("Failed to submit order. Check if /api/create-order exists.");
    }
  };

  const statusIcon = (status: string) => {
    const s = status.toLowerCase();
    if (s === "pass" || s === "safe") return <CheckCircle2 className="h-5 w-5 text-success" />;
    if (s === "warning") return <AlertTriangle className="h-5 w-5 text-warning" />;
    if (s === "danger") return <ShieldAlert className="h-5 w-5 text-destructive" />;
    return null;
  };

  const overallSafe = results && !results.some((r) => r.status.toLowerCase() === "danger");

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8 max-w-2xl">
        <div className="mb-8 animate-fade-in">
          <h1 className="text-3xl font-heading text-foreground">Order Entry</h1>
          <p className="text-muted-foreground mt-1">Create a new prescription and verify safety</p>
        </div>

        <Card className="card-surface animate-fade-in border-light-blue shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 font-heading text-lg">
              <Pill className="h-5 w-5 text-secondary" />
              New Prescription
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-1.5">
              <Label>Patient</Label>
              <Select value={patientId} onValueChange={setPatientId}>
                <SelectTrigger className="bg-white">
                  <SelectValue placeholder="Select patient..." />
                </SelectTrigger>
                <SelectContent className="bg-white">
                  {patients.map((p: any) => (
                    // FIXED: Using p.id and p.name mapped from api.ts
                    <SelectItem key={p.id} value={p.id}>
                      {p.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label>Medication</Label>
              <Select value={drugName} onValueChange={setDrugName}>
                <SelectTrigger className="bg-white">
                  <SelectValue placeholder="Select medication..." />
                </SelectTrigger>
                <SelectContent className="bg-white">
                  {drugs.map((d: any) => (
                    <SelectItem key={d.id} value={d.name}>
                      {d.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="dose">Dosage (mg)</Label>
              <Input 
                id="dose" 
                type="number" 
                value={dose} 
                onChange={(e) => setDose(e.target.value)} 
                placeholder="e.g. 500"
                className="bg-white"
              />
            </div>

            <Button 
              onClick={handleCheck} 
              disabled={checking} 
              className="w-full bg-primary hover:bg-primary/90 text-white transition-all"
            >
              <ShieldCheck className="h-4 w-4 mr-2" />
              {checking ? "Checking..." : "Check Safety"}
            </Button>
          </CardContent>
        </Card>

        {/* Safety Results Modal */}
        <Dialog open={modalOpen} onOpenChange={setModalOpen}>
          <DialogContent className="max-w-lg bg-white">
            <DialogHeader>
              <DialogTitle className="font-heading text-xl flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-secondary" />
                Safety Analysis
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-3 mt-2">
              {(!results || results.length === 0) ? (
                <div className="flex items-start gap-3 p-3 rounded-lg border bg-success/10 border-success/30">
                  <CheckCircle2 className="h-5 w-5 text-success" />
                  <div>
                    <p className="font-medium text-sm">System Check Passed</p>
                    <p className="text-sm text-muted-foreground">No clinical contraindications detected.</p>
                  </div>
                </div>
              ) : (
                results.map((r, i) => (
                  <div key={i} className={`flex items-start gap-3 p-3 rounded-lg border ${
                    r.status.toLowerCase() === "danger" ? "bg-destructive/10 border-destructive/30" :
                    r.status.toLowerCase() === "warning" ? "bg-warning/10 border-warning/30" :
                    "bg-success/10 border-success/30"
                  }`}>
                    {statusIcon(r.status)}
                    <div>
                      <p className="font-medium text-sm">{r.rule}</p>
                      <p className="text-sm text-muted-foreground">{r.message}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
            <div className="flex gap-2 mt-4">
              <Button variant="outline" className="flex-1" onClick={() => setModalOpen(false)}>Cancel</Button>
              <Button 
                className={`flex-1 text-white ${overallSafe ? "bg-success hover:bg-success/90" : "bg-destructive hover:bg-destructive/90"}`} 
                onClick={handleSubmitOrder}
              >
                {overallSafe ? "Submit Order" : "Submit Anyway"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </main>
    </div>
  );
}