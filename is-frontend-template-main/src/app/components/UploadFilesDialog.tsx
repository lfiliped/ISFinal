"use client";

import * as React from 'react';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import { Box, Typography } from '@mui/material';
import { toast } from 'react-toastify';

const UploadFilesDialog = React.forwardRef((props, ref) => {
  const [open, setOpen] = React.useState(false);
  const [file, setFile] = React.useState<File | null>(null);
  const [schemaFile, setSchemaFile] = React.useState<File | null>(null);
  const [loading, setLoading] = React.useState<boolean>(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = event.target.files && event.target.files[0];
    setFile(uploadedFile || null);
  };

  const handleRemoveFile = () => {
    setFile(null);
  };

  const handleSchemaFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = event.target.files && event.target.files[0];
    setSchemaFile(uploadedFile || null);
  };

  const handleSchemaRemoveFile = () => {
    setSchemaFile(null);
  };

  React.useImperativeHandle(ref, () => ({
    handleClickOpen() {
      setOpen(true);
    }
  }));

  const handleClose = () => {
    setOpen(false);
  };

  const handleSubmit = async () => {
    const formData = new FormData();
    if (file) {
      formData.append("file", file);
    }
    if (schemaFile) {
      formData.append("schema_file", schemaFile);
    }
    setLoading(true);
    try {
      const uploadUrl = `${process.env.NEXT_PUBLIC_REST_API_BASE_URL}/api/upload-file/`;
      const response = await fetch(uploadUrl, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        const errorText = await response.text();
        toast.error("Erro no upload dos arquivos: " + errorText);
        return;
      }
      toast.success("Arquivos enviados com sucesso!");
      setFile(null);
      setSchemaFile(null);
    } catch (error: any) {
      console.error("Erro ao enviar arquivos:", error);
      toast.error("Erro ao enviar arquivos. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <React.Fragment>
      <Dialog
        open={open}
        onClose={handleClose}
        aria-labelledby="upload-files-dialog-title"
        aria-describedby="upload-files-dialog-description"
      >
        <DialogTitle id="upload-files-dialog-title">Upload de Arquivos</DialogTitle>
        <DialogContent>
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 2,
              p: 3,
              border: "1px solid #ccc",
              borderRadius: "8px",
            }}
          >
            <Typography variant="h6">Upload de Arquivo .csv</Typography>
            {file ? (
              <>
                <Typography variant="body1">Arquivo Selecionado: {file.name}</Typography>
                <Button variant="contained" color="error" onClick={handleRemoveFile}>
                  Remover Arquivo
                </Button>
              </>
            ) : (
              <Button variant="contained" component="label">
                Selecionar Arquivo .csv
                <input type="file" hidden onChange={handleFileChange} accept=".csv" />
              </Button>
            )}
          </Box>
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 2,
              p: 3,
              border: "1px solid #ccc",
              borderRadius: "8px",
              mt: 1
            }}
          >
            <Typography variant="h6">Upload de Arquivo de Esquema (.xsd)</Typography>
            {schemaFile ? (
              <>
                <Typography variant="body1">Arquivo Selecionado: {schemaFile.name}</Typography>
                <Button variant="contained" color="error" onClick={handleSchemaRemoveFile}>
                  Remover Arquivo
                </Button>
              </>
            ) : (
              <Button variant="contained" component="label">
                Selecionar Arquivo de Esquema
                <input type="file" hidden onChange={handleSchemaFileChange} accept=".xsd, .xmlschema" />
              </Button>
            )}
          </Box>
          {loading && (
            <Typography variant="body2" color="textSecondary" align="center" sx={{ mt: 2 }}>
              Enviando arquivos...
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loading}>Cancelar</Button>
          <Button onClick={handleSubmit} disabled={loading || (!file && !schemaFile)} variant="contained">
            Enviar
          </Button>
        </DialogActions>
      </Dialog>
    </React.Fragment>
  );
});

export default UploadFilesDialog;
