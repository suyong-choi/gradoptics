import math

import torch
from diffoptics.optics.BaseOptics import BaseOptics
from diffoptics.optics.Ray import Rays
from diffoptics.optics.Vector import batch_vector


class Mirror(BaseOptics):

    def __init__(self, x_mirror, y_mirror, z_mirror, normal, mirror_radii):
        super(Mirror, self).__init__()
        self.x_mirror = x_mirror
        self.y_mirror = y_mirror
        self.z_mirror = z_mirror
        self.normal = normal
        self.mirror_radii = mirror_radii

    def _get_plane_equation(self):
        """
        Returns the coefficients of the plane of the mirror ax + by + cz + d = 0
        :return: the coefficients a, b, c and d
        """

        # The equation of a plane containing the point (xm, ym, zm) with normal vector <A, B, C>
        # is given by A(x-xm) + B(y-ym) + C(z-zm) = 0
        a = self.normal[0]
        b = self.normal[1]
        c = self.normal[2]
        d = - self.normal[0] * self.x_mirror - self.normal[1] * self.y_mirror - self.normal[2] * self.z_mirror
        return a, b, c, d

    def get_ray_intersection(self, incident_rays, eps=1e-15):
        """
        Computes the time t at which the incident ray will intersect the mirror
        :param eps:
        :param incident_rays:
        :return:
        """

        # Computes the intersection of the incident_ray with the mirror plane
        origins = incident_rays.origins
        directions = incident_rays.directions
        mirror_plane_coefficients = self._get_plane_equation()
        num = -(mirror_plane_coefficients[0] * origins[:, 0] + mirror_plane_coefficients[1] * origins[:, 1] +
                mirror_plane_coefficients[2] * origins[:, 2] + mirror_plane_coefficients[3])
        den = mirror_plane_coefficients[0] * directions[:, 0] + mirror_plane_coefficients[1] * directions[:, 1] + \
              mirror_plane_coefficients[2] * directions[:, 2]
        t = num / (den + eps)

        # Make sure that the ray hits the mirror
        intersection_points = torch.empty((origins.shape[0], 3), device=incident_rays.device)
        intersection_points[:, 0] = origins[:, 0] + t * directions[:, 0]
        intersection_points[:, 1] = origins[:, 1] + t * directions[:, 1]
        intersection_points[:, 2] = origins[:, 2] + t * directions[:, 2]
        condition = (t > 0) & (
                ((intersection_points[:, 0] - self.x_mirror) ** 2 + (intersection_points[:, 1] - self.y_mirror) ** 2 + (
                        intersection_points[:, 2] - self.z_mirror) ** 2) < self.mirror_radii ** 2)
        # Return nan for rays that have no intersection
        t[~condition] = float('nan')
        return t

    def intersect(self, incident_rays, t):
        """
        Returns the ray reflected by the mirror
        :param incident_rays:
        :param t:
        :return:
        """
        origins = incident_rays.origins
        directions = incident_rays.directions
        collision_points = torch.empty((origins.shape[0], 3), device=incident_rays.device)
        collision_points[:, 0] = origins[:, 0] + directions[:, 0] * t
        collision_points[:, 1] = origins[:, 1] + directions[:, 1] * t
        collision_points[:, 2] = origins[:, 2] + directions[:, 2] * t

        # https://www.fabrizioduroni.it/2017/08/25/how-to-calculate-reflection-vector.html
        directions = -directions
        condition = torch.arccos(
            directions[:, 0] * self.normal[0] + directions[:, 1] * self.normal[1] + directions[:, 2] * self.normal[
                2]) < math.pi / 2
        n = torch.empty((condition.shape[0], 3), device=incident_rays.device)
        n[condition] = self.normal.to(incident_rays.device)
        n[~condition] = -self.normal.to(incident_rays.device)
        scaling = 2 * (directions[:, 0] * n[:, 0] + directions[:, 1] * n[:, 1] + directions[:, 2] * n[:, 2])
        direction_reflected_rays = batch_vector(scaling * n[:, 0] - directions[:, 0],
                                                scaling * n[:, 1] - directions[:, 1],
                                                scaling * n[:, 2] - directions[:, 2])
        reflected_ray = Rays(collision_points,
                             direction_reflected_rays,
                             luminosities=incident_rays.luminosities,
                             device=incident_rays.device)
        return reflected_ray

    def plot(self, ax, show_normal=False, s=0.1, color='lightblue', resolution=100):
        y = torch.arange(-self.mirror_radii, self.mirror_radii, 2 * self.mirror_radii / resolution)
        z = torch.arange(-self.mirror_radii, self.mirror_radii, 2 * self.mirror_radii / resolution)
        y, z = torch.meshgrid(y, z)

        y = y.reshape(-1)
        z = z.reshape(-1)

        indices = (y ** 2 + z ** 2) < self.mirror_radii ** 2
        y = y[indices] + self.y_mirror
        z = z[indices] + self.z_mirror

        # Get z coordinates
        mirror_plane_coefficients = self._get_plane_equation()
        x = (-mirror_plane_coefficients[3] - mirror_plane_coefficients[2] * z - mirror_plane_coefficients[1] * y) / \
            mirror_plane_coefficients[0]

        ax.scatter(x, y, z, s=s, c=color)

        if show_normal:  # @Todo
            pass
