from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
import traceback
from processor_advanced import process_bytes_to_pdf

app = FastAPI(title='Aduragbemi Smart Reader')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.post('/process/')
async def process_file(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        out_pdf = process_bytes_to_pdf(contents, filename=file.filename)
        return StreamingResponse(BytesIO(out_pdf), media_type='application/pdf',
                                 headers={'Content-Disposition': f'attachment; filename="reconstructed_{file.filename}.pdf"'})
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={'error': str(e)})

@app.get('/health')
async def health():
    return {'status': 'ok'}
