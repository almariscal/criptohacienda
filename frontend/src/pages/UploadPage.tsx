import { useNavigate } from 'react-router-dom';
import FileUpload from '../components/FileUpload';
import { apiClient } from '../api/client';
import { useSession } from '../context/SessionContext';

const UploadPage = () => {
  const navigate = useNavigate();
  const { setSessionId } = useSession();

  const handleUpload = async (file: File) => {
    const result = await apiClient.uploadBinanceCsv(file);
    setSessionId(result.session_id);
    navigate('/dashboard');
  };

  return (
    <div>
      <FileUpload onUpload={handleUpload} />
      <div className="alert">Asegúrate de que el CSV corresponde al historial de operaciones de Binance.</div>
    </div>
  );
};

export default UploadPage;
