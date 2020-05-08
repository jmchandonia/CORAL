import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { MockComponent } from 'ng-mocks';
import { DataValuesComponent } from './data-values.component';
import { DataValueFormComponent } from './data-value-form/data-value-form.component';
import { HttpClientModule } from '@angular/common/http';
import { DataValue, Brick } from 'src/app/shared/models/brick';
import { UploadService } from 'src/app/shared/services/upload.service';

describe('DataValuesComponent', () => {

  const MockUploadService = {
    getBrickBuilder: () => new  Brick()
  };

  let spectator: Spectator<DataValuesComponent>;
  const createComponent = createComponentFactory({
    component: DataValuesComponent,
    entryComponents: [
      MockComponent(DataValueFormComponent)
    ],
    imports: [
      HttpClientModule
    ],
    providers: [
      mockProvider(UploadService, MockUploadService)
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
