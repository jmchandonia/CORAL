import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UploadRoutingModule } from './upload-routing.module';
import { UploadComponent } from './upload/upload.component';
import { UploadService } from 'src/app/shared/services/upload.service';
import { TypeSelectorComponent } from './upload/type-selector/type-selector.component';
import { Select2Module } from 'ng2-select2';
import { PropertyBuilderComponent } from './upload/property-builder/property-builder.component';
import { FormsModule } from '@angular/forms';
import { PropertyFormComponent } from './upload/property-builder/property-form/property-form.component';

@NgModule({
  declarations: [UploadComponent, TypeSelectorComponent, PropertyBuilderComponent, PropertyFormComponent],
  imports: [
    CommonModule,
    UploadRoutingModule,
    Select2Module,
    FormsModule
  ],
  providers: [UploadService]
})
export class UploadModule { }
