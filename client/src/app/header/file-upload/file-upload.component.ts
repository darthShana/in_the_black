import { Component } from '@angular/core';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {finalize} from "rxjs";
import {MatCardModule} from '@angular/material/card';
import {MatProgressBar} from "@angular/material/progress-bar";
import {CommonModule} from "@angular/common";
import {MatButton} from "@angular/material/button";
import {AuthService} from "../../service/auth.service";
import {AssistantService} from "../../service/assistant.service";

@Component({
  selector: 'app-file-upload',
  standalone: true,
  imports: [
    MatCardModule,
    MatProgressBar,
    CommonModule,
    MatButton
  ],
  templateUrl: './file-upload.component.html',
  styleUrl: './file-upload.component.scss'
})

export class FileUploadComponent {
  selectedFile: File | null = null;
  uploading = false;

  constructor(private http: HttpClient, private authService: AuthService, private assistantService: AssistantService) {}

  onFileSelected(event: any): void {
    this.selectedFile = event.target.files[0];
  }

  uploadFile(): void {
    if (this.selectedFile) {
      this.uploading = true;
      const formData = new FormData();
      formData.append('file', this.selectedFile, this.selectedFile.name);

      this.authService.getUser().then(user => {
        console.log(user?.access_token)
        if(user && this.selectedFile){

          const headers = new HttpHeaders({
            'Authorization': `Bearer ${user?.access_token}`,
            'Content-Disposition': `attachment; filename="${this.selectedFile.name}"`
          });

          this.http.post('https://jtk21yuyi2.execute-api.us-east-1.amazonaws.com/prod-9c56ae7/document-upload',
            formData,
            { headers: headers, withCredentials: true}
          ).pipe(
            finalize(() => {
              this.uploading = false;
            })
          ).subscribe({
            next: (response) => {
              console.log('File upload success', response)
              this.assistantService.stream(`process transactions from file ${this.selectedFile?.name}`, true, user)
                .then(r => console.log("finished streaming file process"))
            },
            error: (error) => {
              console.error('Error uploading file', error)
            }
          })
        }

      })


    }
  }
}
