import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { addPatient, getPatients } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Plus, Search } from "lucide-react";
import Navbar from "@/components/Navbar";
import { toast } from "sonner";

const emptyForm = () => ({
  patientId: "",
  age: "",
  gender: "",
  condition: "",
  allergy: "",
  currentDrug: "",
  maxSafeDoseMg: "",
});

export default function PatientsPage() {
  const queryClient = useQueryClient();
  const { data: patients = [], isLoading } = useQuery({ queryKey: ["patients"], queryFn: getPatients });
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [submitting, setSubmitting] = useState(false);

  const filtered = patients.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.id.toLowerCase().includes(search.toLowerCase()) ||
    p.condition.toLowerCase().includes(search.toLowerCase())
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.gender) {
      toast.error("Please select a gender.");
      return;
    }
    setSubmitting(true);
    try {
      await addPatient({
        patient_id: form.patientId.trim(),
        age: Number(form.age),
        gender: form.gender,
        condition: form.condition.trim(),
        allergy_class: form.allergy.trim(),
        current_drug: form.currentDrug.trim() || "None",
        max_safe_dose_mg: Number(form.maxSafeDoseMg),
      });
      toast.success("Patient registered");
      setOpen(false);
      setForm(emptyForm());
      await queryClient.invalidateQueries({
        queryKey: ["patients"],
        refetchType: "active",
      });
      await queryClient.refetchQueries({ queryKey: ["patients"] });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not register patient");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <div className="mb-6 flex flex-col gap-4 animate-fade-in sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-3xl font-heading text-foreground">Patient Directory</h1>
            <p className="text-muted-foreground mt-1">Browse and search patient records</p>
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button className="shrink-0">
                <Plus className="h-4 w-4" />
                Add Patient
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <form onSubmit={handleSubmit}>
                <DialogHeader>
                  <DialogTitle>Register new patient</DialogTitle>
                  <DialogDescription>
                    Add a patient record to the database. Patient ID must be unique (e.g. P1001).
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="patient-id">Patient ID</Label>
                    <Input
                      id="patient-id"
                      placeholder="P1001"
                      value={form.patientId}
                      onChange={(e) => setForm((f) => ({ ...f, patientId: e.target.value }))}
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="age">Age</Label>
                    <Input
                      id="age"
                      type="number"
                      min={0}
                      max={130}
                      placeholder="42"
                      value={form.age}
                      onChange={(e) => setForm((f) => ({ ...f, age: e.target.value }))}
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>Gender</Label>
                    <Select
                      value={form.gender || undefined}
                      onValueChange={(v) => setForm((f) => ({ ...f, gender: v }))}
                      required
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select gender" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Male">Male</SelectItem>
                        <SelectItem value="Female">Female</SelectItem>
                        <SelectItem value="Other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="condition">Condition</Label>
                    <Input
                      id="condition"
                      placeholder="Hypertension"
                      value={form.condition}
                      onChange={(e) => setForm((f) => ({ ...f, condition: e.target.value }))}
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="allergy">Allergy</Label>
                    <Input
                      id="allergy"
                      placeholder="Penicillin"
                      value={form.allergy}
                      onChange={(e) => setForm((f) => ({ ...f, allergy: e.target.value }))}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="current-drug">Current drug</Label>
                    <Input
                      id="current-drug"
                      placeholder="Aspirin"
                      value={form.currentDrug}
                      onChange={(e) => setForm((f) => ({ ...f, currentDrug: e.target.value }))}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="max-dose">Max safe dose (mg)</Label>
                    <Input
                      id="max-dose"
                      type="number"
                      min={1}
                      placeholder="500"
                      value={form.maxSafeDoseMg}
                      onChange={(e) => setForm((f) => ({ ...f, maxSafeDoseMg: e.target.value }))}
                      required
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={submitting}>
                    {submitting ? "Saving…" : "Register"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
        <div className="relative mb-4 max-w-sm animate-fade-in">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input className="pl-9" placeholder="Search by name, ID, or condition..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className="card-surface overflow-hidden animate-fade-in">
          <Table>
            <TableHeader>
              <TableRow className="bg-primary/5">
                <TableHead className="font-semibold">ID</TableHead>
                <TableHead className="font-semibold">Name</TableHead>
                <TableHead className="font-semibold">Age</TableHead>
                <TableHead className="font-semibold">Condition</TableHead>
                <TableHead className="font-semibold">Allergy</TableHead>
                <TableHead className="font-semibold">Current Drug</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={6} className="text-center py-8 text-muted-foreground">Loading...</TableCell></TableRow>
              ) : filtered.length === 0 ? (
                <TableRow><TableCell colSpan={6} className="text-center py-8 text-muted-foreground">No patients found.</TableCell></TableRow>
              ) : (
                filtered.map((p) => (
                  <TableRow key={p.id} className="hover:bg-accent/30 transition-colors">
                    <TableCell className="font-mono text-sm">{p.id}</TableCell>
                    <TableCell className="font-medium">{p.name}</TableCell>
                    <TableCell>{p.age}</TableCell>
                    <TableCell>{p.condition}</TableCell>
                    <TableCell>{p.allergy_class ?? p.allergy ?? "—"}</TableCell>
                    <TableCell>{p.current_drug}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </main>
    </div>
  );
}
