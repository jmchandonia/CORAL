import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UploadRoutingModule } from './upload-routing.module';
import { UploadComponent } from './upload/upload.component';
import { UploadService } from 'src/app/shared/services/upload.service';
import { TypeSelectorComponent } from './upload/type-selector/type-selector.component';
import { Select2Module } from 'ng2-select2';

@NgModule({
  declarations: [UploadComponent, TypeSelectorComponent],
  imports: [
    CommonModule,
    UploadRoutingModule,
    Select2Module
  ],
  providers: [UploadService]
})
export class UploadModule { }
