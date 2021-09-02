import numpy as np
import torch

from diffoptics import Rays
from diffoptics.optics import BaseOptics


class BoundingSphere(BaseOptics):

    def __init__(self, radii=1e-3, xc=0.31, yc=0.0, zc=0.0):
        super().__init__()
        self.radii = radii
        self.xc = xc
        self.yc = yc
        self.zc = zc

    def get_ray_intersection(self, incident_rays, eps=1e-15):
        """
        @Todo
        :param incident_rays:
        :param eps:
        :return:
        """

        # Computes the intersection of the incident_ray with the sphere
        origins = incident_rays.origins
        directions = incident_rays.directions
        # Solve the quadratic equation a . t^2 + b . t + c = 0 for t
        # <=> (o_x + t * d_x - self.xc)**2 + (o_y + t * d_y - self.yc)**2 +
        #     (o_z + t * d_z - self.zc)**2 = r**2
        a = directions[:, 0] ** 2 + directions[:, 1] ** 2 + directions[:, 2] ** 2
        b = 2 * ((directions[:, 0] * (origins[:, 0] - self.xc))
                 + (directions[:, 1] * (origins[:, 1] - self.yc))
                 + (directions[:, 2] * (origins[:, 2] - self.zc)))
        c = (origins[:, 0] - self.xc) ** 2 + (origins[:, 1] - self.yc) ** 2 + (
                origins[:, 2] - self.zc) ** 2 - self.radii ** 2
        pho = b ** 2 - 4 * a * c

        # Initialize return values
        t_min = torch.zeros(origins.shape[0]) + float('nan')
        t_max = torch.zeros(origins.shape[0]) + float('nan')

        # Keep the rays that intersect with the sphere
        cond = pho > 0
        t_1 = (- b[cond] + torch.sqrt(pho[cond])) / (2 * a[cond])
        t_2 = (- b[cond] - torch.sqrt(pho[cond])) / (2 * a[cond])

        t_min[cond] = torch.min(t_1, t_2)
        t_max[cond] = torch.max(t_1, t_2)

        # Check that t is greater than 0
        cond_gt_0 = cond & (t_min > eps)
        t_min[~cond_gt_0] = t_max[~cond_gt_0]  # Update negative t with t_max (potentially > 0)
        cond_gt_0 = cond & (t_min > eps)
        t_min[~cond_gt_0] = float('nan')

        return t_min

    def intersect(self, incident_rays, t):
        """
        @Todo
        :param incident_rays:
        :param t:
        :return:
        """

        origins = incident_rays.origins
        directions = incident_rays.directions

        # Update the origin of the incoming rays
        origins = origins + t.unsqueeze(1) * directions

        return Rays(origins,
                    directions,
                    luminosities=incident_rays.luminosities,
                    device=incident_rays.device)

    def plot(self, ax, color='grey', alpha=0.4):
        u = np.linspace(0, 2 * np.pi, 100)
        v = np.linspace(0, np.pi, 100)
        x = self.radii * np.outer(np.cos(u), np.sin(v)) + self.xc
        y = self.radii * np.outer(np.sin(u), np.sin(v)) + self.yc
        z = self.radii * np.outer(np.ones(np.size(u)), np.cos(v)) + self.zc
        ax.plot_surface(x, y, z, color=color, alpha=alpha)
