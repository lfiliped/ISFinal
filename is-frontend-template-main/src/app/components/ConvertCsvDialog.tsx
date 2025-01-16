"use client";

import * as React from "react";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
} from "@mui/material";
import { toast, ToastContainer } from "react-toastify";

interface ConvertCsvDialogProps {}

const ConvertCsvDialog = React.forwardRef((props: ConvertCsvDialogProps, ref) => {
  const [open, setOpen] = React.useState(false);
  const [selectedCsv, setSelectedCsv] = React.useState<string>("");
  const [loading, setLoading] = React.useState<boolean>(false);
  const [conversionResponse, setConversionResponse] = React.useState<string>("");
  const [csvFiles, setCsvFiles] = React.useState<string[]>([]);

  // Permite que o componente seja aberto externamente (como os outros diálogos)
  React.useImperativeHandle(ref, () => ({
    handleClickOpen() {
      setOpen(true);
      // Limpa os estados e carrega a lista ao abrir
      setSelectedCsv("");
      setConversionResponse("");
      fetchCsvFiles();
    },
  }));

  const handleClose = () => {
    setOpen(false);
  };

  // Função para buscar os arquivos CSV disponíveis, usando o endpoint REST que lista arquivos CSV
  const fetchCsvFiles = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_REST_API_BASE_URL}/api/list-csv-files/`
      );
      if (response.ok) {
        const data = await response.json();
        setCsvFiles(data.file_names);
      } else {
        toast.error("Falha ao buscar arquivos CSV.");
      }
    } catch (error) {
      console.error("Erro ao buscar arquivos CSV:", error);
      toast.error("Erro ao buscar arquivos CSV.");
    }
  };

  const handleSubmit = async () => {
    if (!selectedCsv.trim()) {
      toast.error("Por favor, selecione um arquivo CSV.");
      return;
    }

    setLoading(true);
    try {
      // Chama o endpoint para converter CSV para XML (o endpoint espera um JSON com o file_name)
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_REST_API_BASE_URL}/api/convert-csv-to-xml/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ file_name: selectedCsv }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        toast.error(data.error || "Erro na conversão do CSV.");
      } else {
        toast.success("Conversão realizada com sucesso!");
        setConversionResponse(data.message || "");
      }
    } catch (error: any) {
      console.error("Erro ao converter CSV:", error);
      toast.error("Erro ao converter CSV. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <React.Fragment>
      <ToastContainer />
      <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
        <DialogTitle>Converter CSV para XML</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            <FormControl fullWidth>
              <InputLabel id="csv-file-select-label">Arquivo CSV</InputLabel>
              <Select
                labelId="csv-file-select-label"
                value={selectedCsv}
                label="Arquivo CSV"
                onChange={(e) => setSelectedCsv(e.target.value)}
              >
                {csvFiles && csvFiles.length > 0 ? (
                  csvFiles.map((fileName) => (
                    <MenuItem key={fileName} value={fileName}>
                      {fileName}
                    </MenuItem>
                  ))
                ) : (
                  <MenuItem value="" disabled>
                    Nenhum arquivo disponível
                  </MenuItem>
                )}
              </Select>
            </FormControl>
            {loading && (
              <Typography variant="body2" color="textSecondary">
                Processando arquivo...
              </Typography>
            )}
            {conversionResponse && (
              <Box mt={2}>
                <Typography variant="subtitle2">Resposta do Servidor:</Typography>
                <pre
                  style={{
                    backgroundColor: "#f5f5f5",
                    padding: "10px",
                    borderRadius: "5px",
                    overflow: "auto",
                  }}
                >
                  {conversionResponse}
                </pre>
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loading}>
            Cancelar
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={loading || !selectedCsv}
            variant="contained"
          >
            Converter
          </Button>
        </DialogActions>
      </Dialog>
    </React.Fragment>
  );
});

export default ConvertCsvDialog;
