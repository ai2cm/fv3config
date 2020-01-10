from mpi4py import MPI

if __name__ == "__main__":
    assert MPI.COMM_WORLD.Get_size() == 6
    with open(f"rank_{MPI.COMM_WORLD.Get_rank()}", "w") as f:
        pass  # just want to create the file
