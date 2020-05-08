import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { HttpClientModule } from '@angular/common/http';
import { LoadSuccessTableComponent } from './load-success-table.component';
import { Brick } from 'src/app/shared/models/brick';
import { UploadService } from 'src/app/shared/services/upload.service';

describe('LoadSuccessTableComponent', () => {

  const MockUploadService = {
    getBrickBuilder: () => new Brick()
  };

  let spectator: Spectator<LoadSuccessTableComponent>;
  const createComponent = createComponentFactory({
    component: LoadSuccessTableComponent,
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
