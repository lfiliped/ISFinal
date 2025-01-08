"use client";

import * as React from "react";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import { Box, Tab, Tabs, TextField, Select, MenuItem, InputLabel, FormControl } from "@mui/material";
import { Search } from "@mui/icons-material";
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

const XmlViewerDialog = React.forwardRef((_, ref) => {
  const [open, setOpen] = React.useState(false);
  const [value, setValue] = React.useState(0);
  const [xmlFilteredBySearch, setXmlFilteredBySearch] = React.useState<string>(
    "<result></result>"
  );

  const [searchForm, setSearchForm] = React.useState({
    xml_file_name: "",
    search_term: "",
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

  const validateForm = () => {
    if (!searchForm.xml_file_name.trim()) {
      toast.error("Nome do arquivo XML é obrigatório.");
      return false;
    }
    if (!searchForm.search_term.trim()) {
      toast.error("Termo de pesquisa é obrigatório.");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    const params = {
      xml_file_name: searchForm.xml_file_name,
      search_term: searchForm.search_term,
    };

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_REST_API_BASE_URL}/api/xml-text-search/`, { // Atualizado para o endpoint correto
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
      setXmlFilteredBySearch(JSON.stringify(data.results, null, 2)); // Formatar a resposta para exibição
    } catch (error) {
      toast.error("Falha ao buscar resultados. Por favor, tente novamente.");
    }
  };

  return (
    <React.Fragment>
      <ToastContainer />

      <Dialog
        open={open}
        onClose={handleClose}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">{"Visualizador de XML"}</DialogTitle>

        <DialogContent>
          <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
            <Tabs
              value={value}
              onChange={handleChange}
              aria-label="basic tabs example"
            >
              <Tab label="Pesquisa por Texto" {...a11yProps(0)} />
            </Tabs>
          </Box>

          <CustomTabPanel value={value} index={0}>
            <Box className="px-0" component="form" onSubmit={handleSubmit}>
              <FormControl fullWidth margin="normal">
                <InputLabel id="xml-file-name-label">Nome do Arquivo XML</InputLabel>
                <Select
                  labelId="xml-file-name-label"
                  label="Nome do Arquivo XML"
                  value={searchForm.xml_file_name}
                  onChange={(e) =>
                    setSearchForm({ ...searchForm, xml_file_name: e.target.value })
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
                label="Termo de Pesquisa"
                fullWidth
                margin="normal"
                value={searchForm.search_term}
                onChange={(e) =>
                  setSearchForm({ ...searchForm, search_term: e.target.value })
                }
              />

              <Button
                fullWidth
                type="submit"
                variant="contained"
                startIcon={<Search />}
              >
                Buscar
              </Button>
            </Box>

            <pre className="my-4 mx-0" style={{ fontFamily: "monospace" }}>
              <code>{xmlFilteredBySearch}</code>
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

export default XmlViewerDialog;
