import {Component, Input} from '@angular/core';
import {MatIcon} from "@angular/material/icon";
import {CommonModule, NgIf} from "@angular/common";
import {ProfileService} from "../../service/profile.service";

@Component({
  selector: 'app-property-details',
  standalone: true,
  imports: [
    MatIcon,
    NgIf
  ],
  templateUrl: './property-details.component.html',
  styleUrl: './property-details.component.scss'
})
export class PropertyDetailsComponent {

  constructor(protected profileService: ProfileService) {
  }

}
