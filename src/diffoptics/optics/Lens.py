import torch
import numpy as np

from diffoptics.optics.BaseOptics import BaseOptics
from diffoptics.optics.Ray import Rays
from diffoptics.optics.Vector import batch_vector


class PerfectLens(BaseOptics):

    # Assumes that the lens is on the plane x=self.position[0]! Generalization may be required for other usages.

    def __init__(self, f=0.05, na=1 / 1.4, position=torch.tensor([0., 0., 0.]), m=0.15, eps=1e-15):
        super(PerfectLens, self).__init__()
        self.f = f
        self.na = na
        self.position = position
        self.m = m
        self.pof = f * (m + 1) / m
        self.eps = eps

    def get_ray_intersection(self, incident_rays):
        """
        Computes the times t at which the incident rays will intersect the lens
        :param incident_rays:
        :return:
        """
        origins = incident_rays.origins
        directions = incident_rays.directions
        t = (self.position[0] - origins[:, 0]) / (directions[:, 0] + self.eps)
        y = origins[:, 1] + t * directions[:, 1]
        z = origins[:, 2] + t * directions[:, 2]

        # Check that the intersection is real (t>0) and within the lens' bounds
        condition = (t > 0) & (
                ((y - self.position[1]) ** 2 + (z - self.position[2]) ** 2) < (self.f * self.na / 2) ** 2)
        t[~condition] = float('nan')
        return t

    def intersect(self, incident_rays, t):
        """
        Returns the ray refracted by the lens
        @Todo
        :param incident_rays:
        :param t:
        :return:
        """

        optical_center_pos = self.position
        x_objects = incident_rays.origins
        d_0 = incident_rays.directions

        # If x_objects is on the left of the lens, put the plane of focus on the left as well
        pof = self.position[0] + self.pof * torch.sign(x_objects[:, 0] - self.position[0])
        # Put the camera on the opposite side of the lens with respect to x_objects
        camera_pos = self.position[0] - self.f * (1 + self.m) * torch.sign(x_objects[:, 0] - self.position[0])

        # Intersections with the lens
        x_0 = torch.empty((x_objects.shape[0], 3), device=incident_rays.device)
        x_0[:, 0] = x_objects[:, 0] + t * d_0[:, 0]
        x_0[:, 1] = x_objects[:, 1] + t * d_0[:, 1]
        x_0[:, 2] = x_objects[:, 2] + t * d_0[:, 2]

        # computes x_star, the intersections of the rays with the plane of focus
        t = (x_0[:, 0] - pof) / (d_0[:, 0] + self.eps)
        t = -t
        x_star = torch.empty((x_0.shape[0], 3), device=incident_rays.device)
        x_star[:, 0] = x_0[:, 0] + t * d_0[:, 0]
        x_star[:, 1] = x_0[:, 1] + t * d_0[:, 1]
        x_star[:, 2] = x_0[:, 2] + t * d_0[:, 2]

        # Computes x_v, the intersections of the rays coming from x_star and passing trough the optical center with the
        # camera
        # direction along dim 0
        d = torch.empty((x_star.shape[0], 3), device=incident_rays.device)
        d[:, 0] = optical_center_pos[0] - x_star[:, 0]
        d[:, 1] = optical_center_pos[1] - x_star[:, 1]
        d[:, 2] = optical_center_pos[2] - x_star[:, 2]
        t = (camera_pos - x_star[:, 0]) / (d[:, 0] + self.eps)
        x_v = torch.empty((x_star.shape[0], 3), device=incident_rays.device)
        x_v[:, 0] = x_star[:, 0] + t * d[:, 0]
        x_v[:, 1] = x_star[:, 1] + t * d[:, 1]
        x_v[:, 2] = x_star[:, 2] + t * d[:, 2]

        _d_out = batch_vector(x_v[:, 0] - x_0[:, 0], x_v[:, 1] - x_0[:, 1], x_v[:, 2] - x_0[:, 2])
        return Rays(x_0,
                    _d_out,
                    luminosities=incident_rays.luminosities,
                    device=incident_rays.device)

    def sample_points_on_lens(self, nb_points, device='cpu', eps=1e-15):
        """
        Useful for ray marching
        :return:
        """
        points = torch.zeros((nb_points, 3), device=device)
        points[:, 0] = self.position[0]
        lens_radius = self.f * self.na / 2
        # Sampling uniformly on a disk.
        # See https://stats.stackexchange.com/questions/481543/generating-random-points-uniformly-on-a-disk
        r_squared = torch.rand(nb_points, device=device) * lens_radius ** 2
        theta = torch.rand(nb_points, device=device) * 2 * np.pi
        points[:, 1] = torch.sqrt(r_squared + eps) * torch.cos(theta)
        points[:, 2] = torch.sqrt(r_squared + eps) * torch.sin(theta)
        return points

    def plot(self, ax, s=0.1, color='lightblue', resolution=100):
        # @Todo, change this to plot_surface
        y = torch.arange(-self.f * self.na / 2, self.f * self.na / 2, (self.f * self.na) / resolution)
        z = torch.arange(-self.f * self.na / 2, self.f * self.na / 2, (self.f * self.na) / resolution)
        y, z = torch.meshgrid(y, z)

        y = y.reshape(-1)
        z = z.reshape(-1)
        x = torch.zeros(resolution * resolution)

        indices = (y ** 2 + z ** 2) < (self.f * self.na / 2) ** 2
        x = x[indices] + self.position[0]
        y = y[indices] + self.position[1]
        z = z[indices] + self.position[2]

        ax.scatter(x, y, z, s=s, c=color)


class ThickLens(BaseOptics):

    def __init__(self):
        super(ThickLens, self).__init__()
        pass

    @torch.no_grad()
    def get_ray_intersection(self, incident_rays):
        raise NotImplemented

    def intersect(self, incident_rays, t):
        raise NotImplemented

    def sample_points_on_lens(self, nb_points, device='cpu', eps=1e-15):
        raise NotImplemented

    def plot(self, ax):
        raise NotImplemented
