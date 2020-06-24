import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UploadRoutingModule } from './upload-routing.module';
import { UploadComponent } from './upload/upload.component';
import { UploadService } from 'src/app/shared/services/upload.service';
import { TypeSelectorComponent } from './upload/type-selector/type-selector.component';
import { PropertyBuilderComponent } from './upload/property-builder/property-builder.component';
import { FormsModule } from '@angular/forms';
import { PropertyFormComponent } from './upload/property-builder/property-form/property-form.component';
import { DimensionBuilderComponent } from './upload/dimension-builder/dimension-builder.component';
import { DimensionFormComponent } from './upload/dimension-builder/dimension-form/dimension-form.component';
// tslint:disable-next-line:max-line-length
import { DimensionVariableFormComponent } from './upload/dimension-builder/dimension-form/dimension-variable-form/dimension-variable-form.component';
import { LoadComponent } from './upload/load/load.component';
import { UploadDragDropDirective } from 'src/app/shared/directives/upload-drag-drop.directive';
import { DataValuesComponent } from './upload/data-values/data-values.component';
import { DataValueFormComponent } from './upload/data-values/data-value-form/data-value-form.component';
import { NgxSpinnerModule } from 'ngx-spinner';
import { LoadSuccessTableComponent } from './upload/load/load-success-table/load-success-table.component';
import { PreviewComponent } from './upload/preview/preview.component';
import { CreateComponent } from './upload/create/create.component';
import { MapComponent } from './upload/map/map.component';
import { BsDatepickerModule } from 'ngx-bootstrap/datepicker';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { ContextBuilderComponent } from './upload/property-builder/property-form/context-builder/context-builder.component';
import { ContextFormComponent } from './upload/property-builder/property-form/context-builder/context-form/context-form.component';
import { TooltipModule } from 'ngx-bootstrap/tooltip';
import { NgSelectModule } from '@ng-select/ng-select';
import { ValidationErrorItemComponent } from './upload/map/validation-error-item/validation-error-item.component';
 
@NgModule({
  declarations: [
    UploadComponent,
    TypeSelectorComponent,
    PropertyBuilderComponent,
    PropertyFormComponent,
    DimensionBuilderComponent,
    DimensionFormComponent,
    DimensionVariableFormComponent,
    LoadComponent,
    UploadDragDropDirective,
    DataValuesComponent,
    DataValueFormComponent,
    LoadSuccessTableComponent,
    PreviewComponent,
    CreateComponent,
    MapComponent,
    ContextBuilderComponent,
    ContextFormComponent,
    ValidationErrorItemComponent
  ],
  imports: [
    CommonModule,
    BsDatepickerModule.forRoot(),
    NgxSpinnerModule,
    UploadRoutingModule,
    FormsModule,
    BrowserAnimationsModule,
    TooltipModule,
    NgSelectModule
  ],
  providers: [UploadService],
  bootstrap: [
    ContextBuilderComponent,
    ContextFormComponent,
    ValidationErrorItemComponent
  ]
})
export class UploadModule { }
