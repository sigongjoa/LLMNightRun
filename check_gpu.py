"""
Script to check GPU availability and CUDA compatibility without loading any models.
This is a lightweight check that can be run before attempting to load large models.
"""

import sys
import torch
import platform
import subprocess
import os

def format_bytes(bytes):
    """Format bytes to human-readable form"""
    sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    i = 0
    while bytes >= 1024 and i < len(sizes) - 1:
        bytes /= 1024
        i += 1
    return f"{bytes:.2f} {sizes[i]}"

def check_nvidia_smi():
    """Try to run nvidia-smi and capture output"""
    try:
        result = subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except (FileNotFoundError, subprocess.SubprocessError):
        return False, "nvidia-smi command not found or failed to execute"

def check_gpu():
    """Check GPU availability, CUDA support, and print detailed information"""
    print("=" * 50)
    print("GPU COMPATIBILITY CHECK")
    print("=" * 50)
    
    # System information
    print(f"Platform: {platform.platform()}")
    print(f"Python version: {platform.python_version()}")
    print(f"PyTorch version: {torch.__version__}")
    
    # CUDA availability
    cuda_available = torch.cuda.is_available()
    print(f"\nCUDA available: {cuda_available}")
    
    if cuda_available:
        print(f"CUDA version: {torch.version.cuda}")
        
        # Number of GPUs
        gpu_count = torch.cuda.device_count()
        print(f"Number of GPUs available: {gpu_count}")
        
        # GPU information
        for i in range(gpu_count):
            print(f"\nGPU {i} information:")
            print(f"  Name: {torch.cuda.get_device_name(i)}")
            props = torch.cuda.get_device_properties(i)
            print(f"  Total memory: {format_bytes(props.total_memory)}")
            print(f"  CUDA capability: {props.major}.{props.minor}")
            
            # Current memory usage
            try:
                # Get current memory allocated and cached
                memory_allocated = torch.cuda.memory_allocated(i)
                memory_reserved = torch.cuda.memory_reserved(i)
                print(f"  Memory allocated: {format_bytes(memory_allocated)}")
                print(f"  Memory reserved: {format_bytes(memory_reserved)}")
            except (AttributeError, RuntimeError) as e:
                print(f"  Could not get memory usage: {e}")
    else:
        print("\nCUDA is not available. Reasons could be:")
        print("  1. No NVIDIA GPU is installed")
        print("  2. NVIDIA drivers are not installed or outdated")
        print("  3. CUDA toolkit is not installed or version mismatch")
        print("  4. PyTorch was installed without CUDA support")
    
    # Additionally try nvidia-smi for more detailed information
    print("\nRunning nvidia-smi check:")
    success, output = check_nvidia_smi()
    if success:
        print("nvidia-smi output:")
        print("-" * 50)
        print(output)
        print("-" * 50)
    else:
        print("nvidia-smi failed: " + output)
    
    # See if we can create a small tensor on the GPU
    if cuda_available:
        print("\nTesting tensor creation on GPU...")
        try:
            # Try to create a small tensor on GPU
            x = torch.rand(10, 10).cuda()
            print(f"Successfully created tensor on GPU. Shape: {x.shape}, Device: {x.device}")
            
            # Clean up
            del x
            torch.cuda.empty_cache()
        except RuntimeError as e:
            print(f"Failed to create tensor on GPU: {e}")
    
    # Conclusion
    print("\n" + "=" * 50)
    if cuda_available:
        print("RESULT: Your system has CUDA support and GPU is detected.")
        print("You should be able to run models with GPU acceleration.")
    else:
        print("RESULT: No CUDA support detected.")
        print("Models will run on CPU only, which will be much slower.")
    print("=" * 50)

if __name__ == "__main__":
    check_gpu()
