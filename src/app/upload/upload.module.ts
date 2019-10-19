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
import { DimensionBuilderComponent } from './upload/dimension-builder/dimension-builder.component';
import { DimensionFormComponent } from './upload/dimension-builder/dimension-form/dimension-form.component';
// tslint:disable-next-line:max-line-length
import { DimensionVariableFormComponent } from './upload/dimension-builder/dimension-form/dimension-variable-form/dimension-variable-form.component';
import { AsyncDropdownComponent } from './upload/async-dropdown/async-dropdown.component';

@NgModule({
  declarations: [
    UploadComponent,
    TypeSelectorComponent,
    PropertyBuilderComponent,
    PropertyFormComponent,
    DimensionBuilderComponent,
    DimensionFormComponent,
    DimensionVariableFormComponent,
    AsyncDropdownComponent
  ],
  imports: [
    CommonModule,
    UploadRoutingModule,
    Select2Module,
    FormsModule
  ],
  providers: [UploadService]
})
export class UploadModule { }
