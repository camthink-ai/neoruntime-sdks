"""
AI Inference Client
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Tuple

import grpc
import numpy as np

from .config import Config
from .proto import inference_pb2, inference_pb2_grpc


@dataclass
class BoundingBox:
    x: float
    y: float
    width: float
    height: float
    
    def to_xyxy(self) -> Tuple[float, float, float, float]:
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    def to_xywh(self) -> Tuple[float, float, float, float]:
        return (self.x, self.y, self.width, self.height)


@dataclass
class DetectedObject:
    label: str
    score: float
    bbox: BoundingBox
    class_id: int = 0
    track_id: Optional[int] = None


@dataclass
class LandmarkPoint:
    x: float
    y: float
    confidence: float = 1.0


@dataclass
class LandmarkSet:
    type: str
    points: List[LandmarkPoint] = field(default_factory=list)


@dataclass
class Classification:
    type: str
    class_id: int
    label: str
    confidence: float


@dataclass
class SegmentationMask:
    class_id: int
    label: str
    confidence: float
    bbox: BoundingBox
    mask_rle: bytes
    mask_width: int
    mask_height: int

    def to_numpy_mask(self) -> np.ndarray:
        """Decode RLE to HxW bool numpy array."""
        mask = np.zeros(self.mask_width * self.mask_height, dtype=bool)
        i = 0
        data = self.mask_rle
        while i < len(data):
            # Decode varint
            def read_varint(pos):
                val = 0
                shift = 0
                while pos < len(data):
                    b = data[pos]
                    val |= (b & 0x7F) << shift
                    pos += 1
                    if not (b & 0x80):
                        break
                    shift += 7
                return val, pos
            start, i = read_varint(i)
            length, i = read_varint(i)
            mask[start:start + length] = True
        return mask.reshape(self.mask_height, self.mask_width)


@dataclass
class OcrLine:
    text: str
    confidence: float
    bbox: BoundingBox


@dataclass
class Embedding:
    dim: int
    data: List[float]


@dataclass
class DepthMap:
    width: int
    height: int
    data: np.ndarray  # float32 (H, W)


@dataclass
class InferenceResult:
    frame_sequence: int
    timestamp_ns: int
    objects: List[DetectedObject] = field(default_factory=list)
    classifications: List[Classification] = field(default_factory=list)
    landmarks: List[LandmarkSet] = field(default_factory=list)
    masks: List[SegmentationMask] = field(default_factory=list)
    ocr_lines: List[OcrLine] = field(default_factory=list)
    embeddings: List[Embedding] = field(default_factory=list)
    depth_maps: List[DepthMap] = field(default_factory=list)
    raw_outputs: Optional[List[np.ndarray]] = None
    infer_time_us: int = 0
    queue_time_us: int = 0
    hw_infer_time_us: int = 0  # Pure NPU hardware latency (microseconds), 0 if unavailable
    status_message: str = ""  # Diagnostic: "simulation" if no frame source
    
    def has_person(self) -> bool:
        return any(obj.label == "person" for obj in self.objects)
    
    def count_by_label(self, label: str) -> int:
        return sum(1 for obj in self.objects if obj.label == label)
    
    def get_objects_by_label(self, label: str) -> List[DetectedObject]:
        return [obj for obj in self.objects if obj.label == label]


@dataclass
class ModelInfo:
    model_id: str
    model_path: str
    version: str = ""
    inputs: List[Dict] = field(default_factory=list)
    outputs: List[Dict] = field(default_factory=list)
    estimated_tops: float = 0.0
    estimated_memory: int = 0
    load_timestamp: int = 0


@dataclass
class BatchInferItem:
    """A single inference request within a batch."""
    image: np.ndarray
    model_id: str
    timeout_ms: int = 5000
    priority: int = 4


class InferenceClient:
    """
    AI Inference Client

    Usage::

        inf = InferenceClient()

        # Single inference
        result = inf.infer(image, model_id="person_v1")

        # Stream inference
        for frame, res in inf.subscribe(stream="cam0_main", model="person_v1", fps=10):
            print(f"Detected {len(res.objects)} objects")
    """
    
    def __init__(self, endpoint: Optional[str] = None):
        if endpoint is None:
            endpoint = self._get_default_endpoint()
        
        self.endpoint = endpoint
        self.channel: Optional[grpc.Channel] = None
        self.stub: Optional[inference_pb2_grpc.InferenceServiceStub] = None
        
    def _get_default_endpoint(self) -> str:
        import os
        return os.getenv("AI_RUNTIME_ENDPOINT", "unix:///run/aipc/ai-runtime.sock")
    
    def connect(self) -> None:
        if self.channel is None:
            self.channel = grpc.insecure_channel(self.endpoint)
            self.stub = inference_pb2_grpc.InferenceServiceStub(self.channel)

    @property
    def connected(self) -> bool:
        return self.channel is not None
    
    def close(self) -> None:
        if self.channel:
            self.channel.close()
            self.channel = None
            self.stub = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def _numpy_to_tensor(self, arr: np.ndarray, name: str = "") -> inference_pb2.Tensor:
        dtype_map = {
            np.uint8: inference_pb2.UINT8,
            np.int8: inference_pb2.INT8,
            np.uint16: inference_pb2.UINT16,
            np.int16: inference_pb2.INT16,
            np.float16: inference_pb2.FLOAT16,
            np.float32: inference_pb2.FLOAT32,
            np.int32: inference_pb2.INT32,
            np.uint32: inference_pb2.UINT32,
        }
        
        dtype = dtype_map.get(arr.dtype.type, inference_pb2.FLOAT32)
        
        return inference_pb2.Tensor(
            shape=list(arr.shape),
            dtype=dtype,
            data=arr.tobytes()
        )
    
    def _tensor_to_numpy(self, tensor: inference_pb2.Tensor) -> np.ndarray:
        dtype_map = {
            inference_pb2.UINT8: np.uint8,
            inference_pb2.INT8: np.int8,
            inference_pb2.UINT16: np.uint16,
            inference_pb2.INT16: np.int16,
            inference_pb2.FLOAT16: np.float16,
            inference_pb2.FLOAT32: np.float32,
            inference_pb2.INT32: np.int32,
            inference_pb2.UINT32: np.uint32,
        }

        dtype = dtype_map.get(tensor.dtype, np.float32)
        arr = np.frombuffer(tensor.data, dtype=dtype)

        # Handle empty or invalid shape - keep as 1D array
        if tensor.shape and len(tensor.shape) > 0:
            try:
                return arr.reshape(tensor.shape)
            except ValueError:
                # Shape doesn't match data size, return flat array
                return arr
        return arr
    
    def _parse_post_result(self, post_result: inference_pb2.PostResult) -> Tuple[List[DetectedObject], List[Classification], List[LandmarkSet], List[SegmentationMask], List[OcrLine], List[Embedding], List[DepthMap]]:
        objects = []
        for det in post_result.detections:
            obj = DetectedObject(
                label=det.label,
                score=det.confidence,
                bbox=BoundingBox(
                    x=det.bbox.x,
                    y=det.bbox.y,
                    width=det.bbox.w,
                    height=det.bbox.h
                ),
                class_id=det.class_id
            )
            objects.append(obj)

        classifications = []
        for cls in post_result.classifications:
            classifications.append(Classification(
                type=cls.type,
                class_id=cls.class_id,
                label=cls.label,
                confidence=cls.confidence
            ))

        landmarks = []
        for lm_set in post_result.landmarks:
            points = [LandmarkPoint(x=p.x, y=p.y, confidence=p.confidence)
                     for p in lm_set.points]
            landmarks.append(LandmarkSet(type=lm_set.type, points=points))

        masks = []
        for m in post_result.masks:
            masks.append(SegmentationMask(
                class_id=m.class_id,
                label=m.label,
                confidence=m.confidence,
                bbox=BoundingBox(x=m.bbox.x, y=m.bbox.y,
                                 width=m.bbox.w, height=m.bbox.h),
                mask_rle=m.mask_rle,
                mask_width=m.mask_width,
                mask_height=m.mask_height,
            ))

        ocr_lines = []
        for line in post_result.ocr_lines:
            ocr_lines.append(OcrLine(
                text=line.text,
                confidence=line.confidence,
                bbox=BoundingBox(x=line.bbox.x, y=line.bbox.y,
                                 width=line.bbox.w, height=line.bbox.h),
            ))

        embeddings = []
        for emb in post_result.embeddings:
            embeddings.append(Embedding(dim=emb.dim, data=list(emb.data)))

        depth_maps = []
        for dm in post_result.depth_maps:
            arr = np.frombuffer(dm.depth_data, dtype=np.float32).reshape(dm.height, dm.width)
            depth_maps.append(DepthMap(width=dm.width, height=dm.height, data=arr.copy()))

        return objects, classifications, landmarks, masks, ocr_lines, embeddings, depth_maps

    def _parse_infer_response(self, response: inference_pb2.InferResponse) -> InferenceResult:
        """Parse an InferResponse proto into an InferenceResult dataclass.

        Shared by infer() and infer_batch() to avoid duplication.
        """
        objects: List[DetectedObject] = []
        classifications: List[Classification] = []
        landmarks: List[LandmarkSet] = []
        masks: List[SegmentationMask] = []
        ocr_lines: List[OcrLine] = []
        embeddings: List[Embedding] = []
        depth_maps: List[DepthMap] = []

        try:
            if response.HasField('post_result'):
                objects, classifications, landmarks, masks, ocr_lines, embeddings, depth_maps = self._parse_post_result(response.post_result)
        except (ValueError, AttributeError):
            pass

        raw_outputs = None
        if response.outputs:
            raw_outputs = [self._tensor_to_numpy(t) for t in response.outputs]

        return InferenceResult(
            frame_sequence=0,
            timestamp_ns=0,
            objects=objects,
            classifications=classifications,
            landmarks=landmarks,
            masks=masks,
            ocr_lines=ocr_lines,
            embeddings=embeddings,
            depth_maps=depth_maps,
            raw_outputs=raw_outputs,
            infer_time_us=response.infer_time_us,
            queue_time_us=response.queue_time_us,
            hw_infer_time_us=getattr(response, 'hw_infer_time_us', 0),
            status_message=response.status.message if not response.status.success else "",
        )

    def infer(self,
              image: np.ndarray,
              model_id: str,
              timeout_ms: int = 5000,
              priority: int = 4,
              session_id: str = "") -> InferenceResult:
        if self.stub is None:
            self.connect()

        tensor = self._numpy_to_tensor(image, "input")

        request = inference_pb2.InferRequest(
            model_id=model_id,
            inputs=[tensor],
            timeout_ms=timeout_ms,
            priority=priority,
            session_id=session_id
        )

        response = self.stub.Infer(request, timeout=timeout_ms / 1000)

        if not response.status.success:
            raise RuntimeError(f"Inference failed: {response.status.message}")

        return self._parse_infer_response(response)

    def infer_batch(self,
                    items: List[BatchInferItem],
                    timeout_ms: int = 10000) -> List[InferenceResult]:
        """Submit multiple model inferences in a single batch RPC.

        ai-runtime runs them in parallel on the NPU via shared VDevice
        ROUND_ROBIN scheduling, returning all results together.

        Args:
            items: List of (image, model_id, ...) tuples.
            timeout_ms: Overall wall-clock timeout for the entire batch.

        Returns:
            List of InferenceResult, one per item, in the same order.
        """
        if self.stub is None:
            self.connect()

        requests = []
        for item in items:
            tensor = self._numpy_to_tensor(item.image, "input")
            requests.append(inference_pb2.InferRequest(
                model_id=item.model_id,
                inputs=[tensor],
                timeout_ms=item.timeout_ms,
                priority=item.priority,
            ))

        response = self.stub.InferBatch(
            inference_pb2.InferBatchRequest(
                requests=requests,
                timeout_ms=timeout_ms,
            ),
            timeout=timeout_ms / 1000,
        )

        if not response.status.success:
            # Partial failure: still return per-item results
            pass

        results = []
        for resp in response.responses:
            results.append(self._parse_infer_response(resp))
        return results

    def infer_with_tensors(self,
                           model_id: str,
                           inputs: List[np.ndarray],
                           input_names: Optional[List[str]] = None,
                           timeout_ms: int = 5000) -> List[np.ndarray]:
        if self.stub is None:
            self.connect()
        
        if input_names is None:
            input_names = [f"input_{i}" for i in range(len(inputs))]
        
        tensors = [self._numpy_to_tensor(arr, name) 
                   for arr, name in zip(inputs, input_names)]
        
        request = inference_pb2.InferRequest(
            model_id=model_id,
            inputs=tensors,
            timeout_ms=timeout_ms
        )
        
        response = self.stub.Infer(request, timeout=timeout_ms / 1000)
        
        if not response.status.success:
            raise RuntimeError(f"Inference failed: {response.status.message}")
        
        return [self._tensor_to_numpy(t) for t in response.outputs]
    
    def subscribe(self,
                  stream: str,
                  model: str,
                  fps: int = 10,
                  session_id: str = "",
                  raw_output_only: bool = False) -> Iterator[Tuple[int, InferenceResult]]:
        if self.stub is None:
            self.connect()
        
        request = inference_pb2.StreamInferRequest(
            model_id=model,
            stream_id=stream,
            fps_limit=fps,
            session_id=session_id,
            raw_output_only=raw_output_only
        )
        
        for response in self.stub.StreamInfer(request):
            if not response.status.success:
                continue
            
            objects = []
            classifications = []
            landmarks = []
            masks = []
            ocr_lines = []
            embeddings = []
            depth_maps = []

            if response.HasField('post_result'):
                objects, classifications, landmarks, masks, ocr_lines, embeddings, depth_maps = self._parse_post_result(response.post_result)

            raw_outputs = None
            if response.outputs:
                raw_outputs = [self._tensor_to_numpy(t) for t in response.outputs]

            result = InferenceResult(
                frame_sequence=response.frame_sequence,
                timestamp_ns=response.timestamp_ns,
                objects=objects,
                classifications=classifications,
                landmarks=landmarks,
                masks=masks,
                ocr_lines=ocr_lines,
                embeddings=embeddings,
                depth_maps=depth_maps,
                raw_outputs=raw_outputs,
                status_message=response.status.message
            )
            
            yield response.frame_sequence, result
    
    def register_model(self,
                       model_path: str,
                       model_id: Optional[str] = None,
                       owner_id: Optional[str] = None,
                       model_type: Optional[str] = None,
                       model_variant: Optional[str] = None,
                       inputs: Optional[List[Dict]] = None,
                       outputs: Optional[List[Dict]] = None) -> str:
        if self.stub is None:
            self.connect()

        # Translate container path to host path for ai-runtime
        host_path = Config.translate_path_to_host(model_path)

        request = inference_pb2.ModelRegisterRequest(
            model_path=host_path,
            model_id=model_id or ""
        )
        if owner_id:
            request.owner_id = owner_id
        if model_type:
            request.model_type = model_type
        if model_variant:
            request.model_variant = model_variant
        
        if inputs:
            for inp in inputs:
                spec = inference_pb2.TensorSpec(
                    shape=inp.get("shape", []),
                    dtype=self._dtype_str_to_enum(inp.get("dtype", "float32")),
                    name=inp.get("name", "")
                )
                request.inputs.append(spec)
        
        if outputs:
            for out in outputs:
                spec = inference_pb2.TensorSpec(
                    shape=out.get("shape", []),
                    dtype=self._dtype_str_to_enum(out.get("dtype", "float32")),
                    name=out.get("name", "")
                )
                request.outputs.append(spec)
        
        response = self.stub.RegisterModel(request)
        
        if not response.status.success:
            raise RuntimeError(f"Model registration failed: {response.status.message}")
        
        return response.model_id
    
    def _dtype_str_to_enum(self, dtype_str: str) -> int:
        dtype_map = {
            "uint8": inference_pb2.UINT8,
            "int8": inference_pb2.INT8,
            "uint16": inference_pb2.UINT16,
            "int16": inference_pb2.INT16,
            "float16": inference_pb2.FLOAT16,
            "float32": inference_pb2.FLOAT32,
            "int32": inference_pb2.INT32,
            "uint32": inference_pb2.UINT32,
        }
        return dtype_map.get(dtype_str.lower(), inference_pb2.FLOAT32)
    
    def unregister_model(self, model_id: str) -> None:
        if self.stub is None:
            self.connect()
        
        request = inference_pb2.ModelInfo(model_id=model_id)
        response = self.stub.UnregisterModel(request)
        
        if not response.success:
            raise RuntimeError(f"Model unregistration failed: {response.message}")
    
    def list_models(self) -> List[ModelInfo]:
        if self.stub is None:
            self.connect()
        
        response = self.stub.ListModels(inference_pb2.Empty())
        
        models = []
        for m in response.models:
            models.append(ModelInfo(
                model_id=m.model_id,
                model_path=m.model_path,
                version=m.version,
                inputs=[{"shape": list(i.shape), "dtype": i.dtype, "name": i.name} 
                       for i in m.inputs],
                outputs=[{"shape": list(o.shape), "dtype": o.dtype, "name": o.name} 
                        for o in m.outputs],
                estimated_tops=m.estimated_tops,
                estimated_memory=m.estimated_memory,
                load_timestamp=m.load_timestamp
            ))
        
        return models
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        if self.stub is None:
            self.connect()
        
        request = inference_pb2.ModelInfo(model_id=model_id)
        response = self.stub.GetModelInfo(request)
        
        if not response.model_id:
            return None
        
        return ModelInfo(
            model_id=response.model_id,
            model_path=response.model_path,
            version=response.version
        )
    
    def get_stats(self) -> Dict[str, Any]:
        if self.stub is None:
            self.connect()
        
        response = self.stub.GetStats(inference_pb2.Empty())
        
        return {
            "device_utilization": response.device_utilization,
            "device_temperature": response.device_temperature,
            "total_memory_bytes": response.total_memory_bytes,
            "used_memory_bytes": response.used_memory_bytes,
            "cpu_utilization": response.cpu_utilization,
            "dsp_utilization": response.dsp_utilization,
            "ram_total_kib": response.ram_total_kib,
            "ram_used_kib": response.ram_used_kib,
            "model_stats": [
                {
                    "model_id": s.model_id,
                    "total_inferences": s.total_inferences,
                    "total_errors": s.total_errors,
                    "avg_latency_us": s.avg_latency_us,
                    "current_qps": s.current_qps,
                    "queue_depth": s.queue_depth,
                    "hw_fps": getattr(s, 'hw_fps', 0),
                }
                for s in response.model_stats
            ]
        }
    
    def create_session(self, 
                       session_id: str,
                       app_id: str = "",
                       allowed_models: Optional[List[str]] = None,
                       max_qps: int = 0,
                       max_concurrent: int = 0,
                       priority: int = 4) -> str:
        if self.stub is None:
            self.connect()
        
        request = inference_pb2.SessionConfig(
            session_id=session_id,
            app_id=app_id,
            max_qps=max_qps,
            max_concurrent=max_concurrent,
            priority=priority
        )
        
        if allowed_models:
            request.allowed_models.extend(allowed_models)
        
        response = self.stub.CreateSession(request)
        
        if not response.status.success:
            raise RuntimeError(f"Session creation failed: {response.status.message}")
        
        return response.session_id
    
    def destroy_session(self, session_id: str) -> None:
        if self.stub is None:
            self.connect()
        
        request = inference_pb2.SessionConfig(session_id=session_id)
        response = self.stub.DestroySession(request)
        
        if not response.success:
            raise RuntimeError(f"Session destruction failed: {response.message}")

    def update_postprocess_config(self, model_id: str, config_json: str) -> bool:
        """Update postprocess configuration for a model at runtime.

        For CLIP models, config_json can contain:
            {"prompts": ["a person", "a car"], "score_threshold": 0.3}

        Returns True on success.
        """
        if self.stub is None:
            self.connect()

        request = inference_pb2.UpdatePostprocessConfigRequest(
            model_id=model_id,
            config_json=config_json
        )
        response = self.stub.UpdatePostprocessConfig(request)

        if not response.status.success:
            raise RuntimeError(f"UpdatePostprocessConfig failed: {response.status.message}")

        return True

    def encode_text(self, text: str, timeout_ms: int = 5000) -> List[float]:
        """Encode a text string to a CLIP embedding via NPU.

        Returns a list of floats (512-dim for ViT-B/32).
        """
        if self.stub is None:
            self.connect()

        request = inference_pb2.EncodeTextRequest(text=text)
        response = self.stub.EncodeText(request, timeout=timeout_ms / 1000)

        if response.status.code != 0:
            raise RuntimeError(f"EncodeText failed: {response.status.message}")

        return list(response.embedding.data)

    # ── GenAI (LLM/VLM) ──────────────────────────────────────────────────────

    def genai_create_session(self, hef_path: str, kind: str = "llm",
                             lora_name: str = "",
                             optimize_memory: bool = False) -> str:
        """Create a GenAI (LLM/VLM) session.

        Args:
            hef_path: Path to the HEF model file on the device.
            kind: "llm" or "vlm".
            lora_name: Optional LoRA adapter name.
            optimize_memory: Enable memory-optimized tokenization.

        Returns:
            session_id string.
        """
        if self.stub is None:
            self.connect()

        host_path = Config.translate_path_to_host(hef_path)
        kind_map = {"llm": 0, "vlm": 1}
        request = inference_pb2.GenaiCreateSessionRequest(
            hef_path=host_path,
            kind=kind_map.get(kind, 0),
            lora_name=lora_name,
            optimize_memory=optimize_memory
        )
        response = self.stub.GenaiCreateSession(request, timeout=300)

        if response.status.code != 0:
            raise RuntimeError(f"GenAI create session failed: {response.status.message}")

        return response.session_id

    def genai_destroy_session(self, session_id: str) -> None:
        """Destroy a GenAI session and free resources."""
        if self.stub is None:
            self.connect()

        # hef_path is reused as session_id carrier for destroy
        request = inference_pb2.GenaiCreateSessionRequest(hef_path=session_id)
        response = self.stub.GenaiDestroySession(request, timeout=10)

        if response.code != 0:
            raise RuntimeError(f"GenAI destroy session failed: {response.message}")

    def genai_generate(self, session_id: str, messages: List[str],
                       images: Optional[List[bytes]] = None,
                       stop_tokens: Optional[List[str]] = None,
                       temperature: float = 0.0,
                       top_p: float = 1.0,
                       top_k: int = 0,
                       max_tokens: int = 512,
                       do_sample: bool = False) -> Iterator[str]:
        """Stream generated tokens from a GenAI session.

        Args:
            session_id: Session from genai_create_session().
            messages: List of JSON-encoded chat messages.
            images: Optional RGB image frames for VLM.
            stop_tokens: Optional stop sequences.
            temperature, top_p, top_k, max_tokens, do_sample: Generation params.

        Yields:
            Token strings as they are generated.
        """
        if self.stub is None:
            self.connect()

        request = inference_pb2.GenaiGenerateRequest(
            session_id=session_id,
            messages_json=messages,
            image_frames=images or [],
            stop_tokens=stop_tokens or [],
        )
        if do_sample or temperature > 0 or max_tokens != 512:
            request.params.temperature = temperature
            request.params.top_p = top_p
            request.params.top_k = top_k
            request.params.max_generated_tokens = max_tokens
            request.params.do_sample = do_sample

        for resp in self.stub.GenaiGenerate(request):
            if resp.HasField('token'):
                yield resp.token
            elif resp.HasField('finish'):
                break

    def genai_abort(self, session_id: str) -> None:
        """Abort an ongoing generation."""
        if self.stub is None:
            self.connect()

        request = inference_pb2.GenaiAbortRequest(session_id=session_id)
        self.stub.GenaiAbort(request, timeout=5)