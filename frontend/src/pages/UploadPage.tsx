import { useNavigate } from 'react-router-dom';
import FileUpload from '../components/FileUpload';
import { apiClient } from '../api/client';
import { useSession } from '../context/SessionContext';

const UploadPage = () => {
  const navigate = useNavigate();
  const { setSessionId } = useSession();

  const handleUploadStart = async (file: File) => {
    const result = await apiClient.uploadBinanceCsv(file);
    return result.job_id;
  };

  const handleUploadComplete = (sessionId: string) => {
    setSessionId(sessionId);
    navigate('/dashboard');
  };

  return (
    <div className="upload-stack">
      <FileUpload onUploadStart={handleUploadStart} onUploadComplete={handleUploadComplete} />
      <div className="panel panel-info">
        <h3>Consejos rápidos</h3>
        <p>Descarga el CSV desde Binance &gt; Orders &gt; Spot Trading &gt; Trade History. No modificas columnas ni encabezados.</p>
        <ul className="tips-list">
          <li>Solo se procesa localmente; puedes eliminar la sesión cuando quieras.</li>
          <li>El modo noche ajusta la interfaz sin alterar tus datos.</li>
        </ul>
      </div>
    </div>
  );
};

export default UploadPage;
