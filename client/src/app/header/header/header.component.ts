import {Component, OnDestroy, OnInit} from '@angular/core';
import {MatIcon} from "@angular/material/icon";
import {PropertyDetailsComponent} from "../property-details/property-details.component";
import {CommonModule} from "@angular/common";
import {FileUploadComponent} from "../file-upload/file-upload.component";

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [
    MatIcon,
    CommonModule,
    PropertyDetailsComponent,
    FileUploadComponent
  ],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss'
})
export class HeaderComponent  {



}
