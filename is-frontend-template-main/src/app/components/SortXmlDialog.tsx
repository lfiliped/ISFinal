"use client";

import * as React from "react";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import { Box, Tab, Tabs, TextField, FormControl, InputLabel, Select, MenuItem } from "@mui/material";
import { Sort } from "@mui/icons-material";
import { toast, ToastContainer } from "react-toastify";

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function CustomTabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `simple-tab-${index}`,
    "aria-controls": `simple-tabpanel-${index}`,
  };
}

const SortXmlDialog = React.forwardRef((_, ref) => {
  const [open, setOpen] = React.useState(false);
  const [value, setValue] = React.useState(0);
  const [sortedXml, setSortedXml] = React.useState<string>("<result></result>");

  const [sortForm, setSortForm] = React.useState({
    xml_file_name: "",
    sort_by: "",
    order: "asc",
  });

  const [xmlFiles, setXmlFiles] = React.useState<string[]>([]); // Estado para armazenar a lista de arquivos XML

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  React.useImperativeHandle(ref, () => ({
    handleClickOpen() {
      setOpen(true);
    },
  }));

  const handleClose = () => {
    setOpen(false);
  };

  const validateForm = () => {
    if (!sortForm.xml_file_name.trim()) {
      toast.error("Nome do arquivo XML é obrigatório.");
      return false;
    }
    if (!sortForm.sort_by.trim()) {
      toast.error("Campo de ordenação é obrigatório.");
      return false;
    }
    return true;
  };

  // Função para buscar os arquivos XML disponíveis (similar ao XmlViewerDialog)
  const fetchXMLFiles = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_REST_API_BASE_URL}/api/list-xml-files/`);
      if (response.ok) {
        const data = await response.json();
        setXmlFiles(data.file_names);
      } else {
        toast.error("Falha ao buscar arquivos XML.");
      }
    } catch (error) {
      console.error("Erro ao buscar arquivos XML:", error);
      toast.error("Erro ao buscar arquivos XML.");
    }
  };

  React.useEffect(() => {
    if (open) {
      fetchXMLFiles();
    }
  }, [open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    const params = {
      xml_file_name: sortForm.xml_file_name,
      sort_by: sortForm.sort_by,
      order: sortForm.order,
    };

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_REST_API_BASE_URL}/api/sort-xml/`, { // Atualizado para usar a variável de ambiente
        method: "POST",
        body: JSON.stringify(params),
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const error = await response.json();
        toast.error(error.message || "Ocorreu um erro.");
        return;
      }

      const data = await response.json();
      setSortedXml(data.sorted_xml); // Ajuste conforme a resposta do backend
      toast.success("XML ordenado com sucesso!");
    } catch (error) {
      console.error("Erro ao ordenar XML:", error);
      toast.error("Falha ao ordenar XML. Por favor, tente novamente.");
    }
  };

  return (
    <React.Fragment>
      <ToastContainer />

      <Dialog
        open={open}
        onClose={handleClose}
        aria-labelledby="sort-xml-dialog-title"
        aria-describedby="sort-xml-dialog-description"
      >
        <DialogTitle id="sort-xml-dialog-title">{"Ordenar XML"}</DialogTitle>

        <DialogContent>
          <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
            <Tabs
              value={value}
              onChange={handleChange}
              aria-label="sort xml tabs"
            >
              <Tab label="Ordenar XML" {...a11yProps(0)} />
            </Tabs>
          </Box>

          <CustomTabPanel value={value} index={0}>
            <Box className="px-0" component="form" onSubmit={handleSubmit}>
              <FormControl fullWidth margin="normal">
                <InputLabel id="xml-file-name-label">Nome do Arquivo XML</InputLabel>
                <Select
                  labelId="xml-file-name-label"
                  label="Nome do Arquivo XML"
                  value={sortForm.xml_file_name}
                  onChange={(e) =>
                    setSortForm({ ...sortForm, xml_file_name: e.target.value })
                  }
                >
                  {xmlFiles.length > 0 ? (
                    xmlFiles.map((fileName) => (
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

              <TextField
                label="Campo para Ordenar"
                fullWidth
                margin="normal"
                value={sortForm.sort_by}
                onChange={(e) =>
                  setSortForm({ ...sortForm, sort_by: e.target.value })
                }
              />
              <FormControl fullWidth margin="normal">
                <InputLabel id="order-select-label">Ordem</InputLabel>
                <Select
                  labelId="order-select-label"
                  id="order-select"
                  value={sortForm.order}
                  label="Ordem"
                  onChange={(e) =>
                    setSortForm({ ...sortForm, order: e.target.value as string })
                  }
                >
                  <MenuItem value="asc">Ascendente</MenuItem>
                  <MenuItem value="desc">Descendente</MenuItem>
                </Select>
              </FormControl>

              <Button
                fullWidth
                type="submit"
                variant="contained"
                startIcon={<Sort />}
              >
                Ordenar
              </Button>
            </Box>

            <pre className="my-4 mx-0" style={{ fontFamily: "monospace" }}>
              <code>{sortedXml}</code>
            </pre>
          </CustomTabPanel>
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClose}>Cancelar</Button>
        </DialogActions>
      </Dialog>
    </React.Fragment>
  );
});

export default SortXmlDialog;
